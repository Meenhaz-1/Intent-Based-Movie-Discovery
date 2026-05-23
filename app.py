import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import tmdb_helper

load_dotenv()

CHECKPOINTS_DIR = Path("checkpoints")
MOVIELENS_DIR = Path("data/movielens")

REQUIRED_FILES = [
    CHECKPOINTS_DIR / "embeddings.npy",
    CHECKPOINTS_DIR / "faiss_index.bin",
    CHECKPOINTS_DIR / "movie_ids.csv",
    MOVIELENS_DIR / "movies.csv",
    MOVIELENS_DIR / "tags.csv",
]


st.set_page_config(page_title="Movie Search and Recommendations", layout="wide")

st.title("Movie Search and Recommendations")
st.caption("Search by title, theme, or similarity, then build a small local taste profile.")


def stop_if_setup_is_incomplete():
    missing = [path for path in REQUIRED_FILES if not path.exists()]
    if not missing:
        return

    st.error("The local data and checkpoint files are not ready yet.")
    st.write("Run the notebooks in order, starting with `phase_1.ipynb`, then come back to the app.")
    st.write("Missing files:")
    st.code("\n".join(str(path) for path in missing), language="text")
    st.info("See `docs/QUICKSTART.md` for the full setup path.")
    st.stop()


stop_if_setup_is_incomplete()


@st.cache_resource(show_spinner="Loading movie index...")
def load_artifacts():
    embeddings = np.load(CHECKPOINTS_DIR / "embeddings.npy")
    faiss_index = faiss.read_index(str(CHECKPOINTS_DIR / "faiss_index.bin"))
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    movie_ids_df = pd.read_csv(CHECKPOINTS_DIR / "movie_ids.csv")
    movies_df = pd.read_csv(MOVIELENS_DIR / "movies.csv")
    tags_df = pd.read_csv(MOVIELENS_DIR / "tags.csv")

    movie_ids_df = movie_ids_df.merge(movies_df[["movieId", "genres"]], on="movieId", how="left")
    movie_ids_df["genres"] = movie_ids_df["genres"].fillna("")

    tags_by_movie = tags_df.dropna(subset=["tag"]).groupby("movieId")["tag"].apply(" ".join).to_dict()
    combined_text = {}
    for _, row in movie_ids_df.iterrows():
        movie_id = row["movieId"]
        genres = row.get("genres", "")
        tags = tags_by_movie.get(movie_id, "")
        combined_text[movie_id] = f"{genres} {tags}".strip()

    corpus = [combined_text.get(movie_id, "") for movie_id in movie_ids_df["movieId"]]
    tokenized_corpus = [doc.lower().split() for doc in corpus]

    return {
        "embeddings": embeddings,
        "faiss_index": faiss_index,
        "embedding_model": embedding_model,
        "movies_df": movie_ids_df,
        "bm25": BM25Okapi(tokenized_corpus),
    }


artifacts = load_artifacts()
embeddings = artifacts["embeddings"]
faiss_index = artifacts["faiss_index"]
embedding_model = artifacts["embedding_model"]
movies_df = artifacts["movies_df"]
bm25 = artifacts["bm25"]


def init_user_store():
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CHECKPOINTS_DIR / "user_preferences.sqlite")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS user_likes (
            user_id TEXT,
            movie_id INTEGER,
            liked_at TIMESTAMP,
            review_text TEXT,
            PRIMARY KEY (user_id, movie_id)
        )"""
    )
    conn.commit()
    return conn


conn = init_user_store()


def extract_release_year(title):
    match = re.search(r"\((\d{4})\)\s*$", title)
    return int(match.group(1)) if match else None


def display_movie_card(title, genres, score):
    col1, col2 = st.columns([1, 3])
    movie_info = tmdb_helper.fetch_movie_info(title, extract_release_year(title))

    with col1:
        if movie_info and movie_info.get("poster_url"):
            st.image(movie_info["poster_url"], width=150)
        else:
            st.write("No poster")

    with col2:
        st.markdown(f"**{title}**")
        st.caption(genres if genres else "N/A")

        if movie_info:
            st.markdown(
                f"Rating: {movie_info.get('rating', 0):.1f} "
                f"({movie_info.get('vote_count', 0)} votes)"
            )
            st.caption(f"Released: {movie_info.get('release_date', 'Unknown')}")

            if movie_info.get("plot"):
                st.write(f"Plot: {movie_info['plot'][:200]}...")

            if movie_info.get("cast"):
                st.caption(f"Cast: {', '.join(movie_info['cast'][:3])}")

        st.markdown(f"**Score**: {score}")

    st.divider()


def get_user_likes(user_id):
    df = pd.read_sql_query(
        "SELECT movie_id FROM user_likes WHERE user_id = ?",
        conn,
        params=(user_id,),
    )
    return df["movie_id"].tolist() if len(df) > 0 else []


st.sidebar.markdown("### User Profile")
user_id = st.sidebar.text_input("Your ID", value="demo_user")

st.sidebar.markdown("### TMDB Setup")
tmdb_key_env = os.getenv("TMDB_API_KEY", "").strip()

if tmdb_key_env:
    tmdb_helper.set_api_key(tmdb_key_env)
    st.sidebar.success("TMDB connected from .env")
else:
    tmdb_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="Get one from themoviedb.org")
    if tmdb_key:
        tmdb_helper.set_api_key(tmdb_key)
        st.sidebar.success("TMDB connected")
    else:
        st.sidebar.info("Add TMDB_API_KEY to .env or enter a key here to see posters.")

liked_ids = get_user_likes(user_id)
st.sidebar.metric("Movies Liked", len(liked_ids))

tab1, tab2, tab3, tab4 = st.tabs(["Search", "Similar", "My Likes", "Recommendations"])


with tab1:
    st.subheader("Search for Movies")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        query = st.text_input("Enter a search query", placeholder="Interstellar or space exploration")
    with col2:
        search_type = st.selectbox("Find", ["Movie or Theme", "Title Only", "Theme Only"], label_visibility="collapsed")
    with col3:
        approach = st.selectbox("Method", ["Semantic", "Keyword (BM25)"], label_visibility="collapsed")

    if query:
        n = st.slider("Results", 5, 20, 10)
        results = []
        seen_movie_ids = set()

        if search_type in ["Movie or Theme", "Title Only"]:
            title_matches = movies_df[
                movies_df["title"].str.lower().str.contains(query.lower(), regex=False, na=False)
            ].head(1)
            for _, row in title_matches.iterrows():
                results.append(
                    {
                        "movieId": row["movieId"],
                        "Title": row["title"],
                        "Genres": row.get("genres", "N/A"),
                        "Score": "Exact title match",
                    }
                )
                seen_movie_ids.add(row["movieId"])

        if search_type in ["Movie or Theme", "Theme Only"]:
            if approach == "Semantic":
                query_emb = embedding_model.encode(query, convert_to_numpy=True)
                query_emb = query_emb / np.linalg.norm(query_emb)
                distances, indices = faiss_index.search(query_emb.astype("float32").reshape(1, -1), n + 5)

                for pos, idx in enumerate(indices[0]):
                    movie = movies_df.iloc[idx]
                    if movie["movieId"] in seen_movie_ids:
                        continue
                    results.append(
                        {
                            "movieId": movie["movieId"],
                            "Title": movie["title"],
                            "Genres": movie.get("genres", "N/A"),
                            "Score": f"{distances[0][pos]:.3f}",
                        }
                    )
                    seen_movie_ids.add(movie["movieId"])
                    if len(results) >= n:
                        break
                st.markdown("#### Semantic Search Results")
            else:
                scores = bm25.get_scores(query.lower().split())
                top_idx = np.argsort(scores)[::-1]
                for idx in top_idx:
                    movie = movies_df.iloc[idx]
                    if movie["movieId"] in seen_movie_ids:
                        continue
                    results.append(
                        {
                            "movieId": movie["movieId"],
                            "Title": movie["title"],
                            "Genres": movie.get("genres", "N/A"),
                            "Score": f"{scores[idx]:.3f}" if scores[idx] > 0 else "0.000",
                        }
                    )
                    seen_movie_ids.add(movie["movieId"])
                    if len(results) >= n:
                        break
                st.markdown("#### Keyword Search Results")

        if results:
            st.markdown("#### Results")
            for result in results[:n]:
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    display_movie_card(result["Title"], result["Genres"], result["Score"])
                with col_right:
                    if st.button("Add", key=f"add_{result['movieId']}"):
                        conn.execute(
                            "INSERT OR REPLACE INTO user_likes (user_id, movie_id, liked_at) VALUES (?, ?, ?)",
                            (user_id, int(result["movieId"]), datetime.now()),
                        )
                        conn.commit()
                        st.success(f"Added '{result['Title']}'")
                        st.rerun()
        else:
            st.warning("No results found.")


with tab2:
    st.subheader("Find Similar Movies")
    selected_movie = st.selectbox("Pick a movie", movies_df["title"].values)

    if selected_movie:
        movie_idx = movies_df[movies_df["title"] == selected_movie].index[0]
        n = st.slider("Count", 5, 20, 10)

        movie_emb = embeddings[movie_idx].astype("float32").reshape(1, -1)
        distances, indices = faiss_index.search(movie_emb, n + 1)

        st.markdown("#### Similar Movies")
        for rank, idx in enumerate(indices[0][1:]):
            if rank >= n:
                break
            movie = movies_df.iloc[idx]
            col_left, col_right = st.columns([2, 1])
            with col_left:
                display_movie_card(movie["title"], movie.get("genres", "N/A"), f"{distances[0][rank + 1]:.3f}")
            with col_right:
                if st.button("Like", key=f"like_{movie['movieId']}"):
                    conn.execute(
                        "INSERT OR REPLACE INTO user_likes (user_id, movie_id, liked_at) VALUES (?, ?, ?)",
                        (user_id, int(movie["movieId"]), datetime.now()),
                    )
                    conn.commit()
                    st.success(f"Added '{movie['title']}'")
                    st.rerun()


with tab3:
    st.subheader("Your Liked Movies")

    if liked_ids:
        st.markdown(f"#### Your {len(liked_ids)} Liked Movies")
        for pos, movie_id in enumerate(liked_ids, start=1):
            movie = movies_df[movies_df["movieId"] == movie_id]
            if len(movie) == 0:
                continue

            col_left, col_right = st.columns([2, 1])
            with col_left:
                display_movie_card(movie.iloc[0]["title"], movie.iloc[0].get("genres", "N/A"), f"#{pos}")
            with col_right:
                if st.button("Remove", key=f"remove_{movie_id}"):
                    conn.execute("DELETE FROM user_likes WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
                    conn.commit()
                    st.success("Removed")
                    st.rerun()

        st.metric("Progress", f"{len(liked_ids)}/15 movies", delta="More likes can improve recommendations")

        if st.button("Clear All Likes"):
            conn.execute("DELETE FROM user_likes WHERE user_id = ?", (user_id,))
            conn.commit()
            st.success("Cleared all likes")
            st.rerun()
    else:
        st.info("Use the Search tab to add movies you like.")


with tab4:
    st.subheader("Personalized Recommendations")
    st.caption("The app uses a content-based taste vector from your liked movies.")

    if len(liked_ids) == 0:
        st.info("Use the Search tab to find and like movies.")
    elif len(liked_ids) < 2:
        st.warning(f"Add {2 - len(liked_ids)} more movie(s) to see recommendations.")
    else:
        n = st.slider("Show", 5, 20, 10)

        indices_list = []
        for movie_id in liked_ids:
            idx = movies_df[movies_df["movieId"] == movie_id].index
            if len(idx) > 0:
                indices_list.append(idx[0])

        if indices_list:
            user_emb = embeddings[indices_list].mean(axis=0)
            norm = np.linalg.norm(user_emb)
            if norm == 0:
                st.error("Could not build a preference vector from these likes.")
                st.stop()

            user_emb = user_emb / norm
            distances, indices = faiss_index.search(user_emb.astype("float32").reshape(1, -1), n + len(liked_ids))

            st.markdown(f"#### Based on Your {len(liked_ids)} Likes")
            rec_count = 0
            for pos, idx in enumerate(indices[0]):
                if rec_count >= n:
                    break
                movie = movies_df.iloc[idx]
                if movie["movieId"] in liked_ids:
                    continue

                col_left, col_right = st.columns([2, 1])
                with col_left:
                    display_movie_card(movie["title"], movie.get("genres", "N/A"), f"{distances[0][pos]:.3f}")
                with col_right:
                    if st.button("Add", key=f"rec_{movie['movieId']}"):
                        conn.execute(
                            "INSERT OR REPLACE INTO user_likes (user_id, movie_id, liked_at) VALUES (?, ?, ?)",
                            (user_id, int(movie["movieId"]), datetime.now()),
                        )
                        conn.commit()
                        st.success(f"Added '{movie['title']}'")
                        st.rerun()
                rec_count += 1
        else:
            st.error("Could not generate recommendations from the saved likes.")


st.markdown("---")
st.markdown(
    """**How it works**

- Search compares semantic embeddings with BM25 keyword matching.
- Similar movies come from the FAISS embedding index.
- Likes are stored locally in SQLite.
- Recommendations in the app use a content-based user vector; Phase 4 explores collaborative filtering as a notebook experiment.
"""
)
