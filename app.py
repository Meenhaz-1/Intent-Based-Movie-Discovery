import os
import re
import sqlite3
import warnings
from datetime import datetime
from pathlib import Path

# Suppress unnecessary warnings from transformers library
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import faiss
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import tmdb_helper
import db_migration
import recommendations

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

RECENCY_HALF_LIFE_YEARS = 20
RECENCY_WEIGHT = 0.20
RELEVANCE_WEIGHT = 0.80


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


@st.cache_resource
def init_user_store():
    """Cache database connection across reruns."""
    return db_migration.init_database(CHECKPOINTS_DIR / "user_preferences.sqlite")


conn = init_user_store()


def extract_release_year(title):
    match = re.search(r"\((\d{4})\)\s*$", title)
    return int(match.group(1)) if match else None


def filter_by_year(movies_list, min_year, max_year):
    """Filter movies by release year."""
    filtered = []
    for movie in movies_list:
        year = extract_release_year(movie.get("Title", ""))
        if year and min_year <= year <= max_year:
            filtered.append(movie)
    return filtered


def calculate_freshness(title):
    release_year = extract_release_year(title)
    if release_year is None:
        return 0.0

    age_years = max(0, datetime.now().year - release_year)
    return 0.5 ** (age_years / RECENCY_HALF_LIFE_YEARS)


def normalize_scores(scores):
    scores = np.asarray(scores, dtype=float)
    if len(scores) == 0:
        return scores

    finite_scores = scores[np.isfinite(scores)]
    if len(finite_scores) == 0:
        return np.zeros_like(scores)

    min_score = finite_scores.min()
    max_score = finite_scores.max()
    if np.isclose(max_score, min_score):
        return np.ones_like(scores)

    normalized = (scores - min_score) / (max_score - min_score)
    return np.nan_to_num(normalized, nan=0.0, posinf=1.0, neginf=0.0)


def rank_with_recency(candidates):
    relevance_scores = [candidate["relevance_score"] for candidate in candidates]
    normalized_scores = normalize_scores(relevance_scores)
    ranked = []

    for candidate, normalized_score in zip(candidates, normalized_scores):
        freshness = calculate_freshness(candidate["movie"]["title"])
        adjusted_score = (RELEVANCE_WEIGHT * normalized_score) + (RECENCY_WEIGHT * freshness)
        ranked.append(
            {
                **candidate,
                "adjusted_score": adjusted_score,
                "freshness_score": freshness,
                "normalized_relevance": normalized_score,
            }
        )

    return sorted(ranked, key=lambda item: item["adjusted_score"], reverse=True)


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


@st.cache_data(ttl=300)
def get_profile_likes_cached(profile_id):
    """Get all liked movie IDs for a profile (cached for 5 minutes)."""
    return db_migration.get_profile_likes(conn, profile_id)


def get_profile_likes(profile_id):
    """Get profile likes with optional cache invalidation."""
    # Use session state flag to invalidate cache when needed
    if st.session_state.get("invalidate_likes_cache"):
        st.cache_data.clear()
        st.session_state.invalidate_likes_cache = False
    return get_profile_likes_cached(profile_id)


# ============================================================================
# User & Profile Management (Optimized)
# ============================================================================

st.sidebar.markdown("### Account")
user_id = st.sidebar.text_input("User ID", value="demo_user", key="user_id_input")

# Cache profile list in session state to avoid repeated queries
if "last_user_id" not in st.session_state or st.session_state.last_user_id != user_id:
    st.session_state.last_user_id = user_id
    st.session_state.user_profiles = None

# Load profiles (with session state caching)
if st.session_state.user_profiles is None:
    user_profiles = db_migration.get_user_profiles(conn, user_id)

    # Ensure default profile exists
    if not user_profiles:
        try:
            db_migration.create_profile(conn, user_id, "Default Profile")
            user_profiles = db_migration.get_user_profiles(conn, user_id)
        except sqlite3.IntegrityError:
            user_profiles = db_migration.get_user_profiles(conn, user_id)

    st.session_state.user_profiles = user_profiles
else:
    user_profiles = st.session_state.user_profiles

if user_profiles:
    # Profile selector
    profile_options = {p["profile_id"]: f"{p['profile_name']} ({p['like_count']} likes)" for p in user_profiles}

    if "selected_profile_id" not in st.session_state:
        st.session_state.selected_profile_id = user_profiles[0]["profile_id"]

    selected_profile_id = st.sidebar.selectbox(
        "Select Profile",
        options=list(profile_options.keys()),
        format_func=lambda pid: profile_options[pid],
        key="profile_selector",
    )
    st.session_state.selected_profile_id = selected_profile_id
else:
    st.sidebar.warning("No profiles found. Creating default...")
    default_pid = db_migration.create_profile(conn, user_id, "Default Profile")
    st.session_state.user_profiles = None
    st.rerun()

# Manage profiles
with st.sidebar.expander("Manage Profiles", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("New", key="new_profile_btn"):
            st.session_state.show_new_profile_modal = True

    with col2:
        if st.button("Rename", key="rename_profile_btn"):
            st.session_state.show_rename_modal = True

    with col3:
        if len(user_profiles) > 1:
            if st.button("Delete", key="delete_profile_btn"):
                db_migration.delete_profile(conn, selected_profile_id)
                st.session_state.user_profiles = None
                st.success("Profile deleted!")
                st.rerun()

# Create new profile modal
if st.session_state.get("show_new_profile_modal"):
    new_profile_name = st.sidebar.text_input("Profile name", placeholder="e.g., Partner, Kids", key="new_profile_name_input")
    if st.sidebar.button("Create Profile", key="create_profile_confirm"):
        if new_profile_name.strip():
            db_migration.create_profile(conn, user_id, new_profile_name)
            st.session_state.user_profiles = None
            st.session_state.show_new_profile_modal = False
            st.success(f"Created profile '{new_profile_name}'")
            st.rerun()

# Rename profile modal
if st.session_state.get("show_rename_modal"):
    current_name = next(p["profile_name"] for p in user_profiles if p["profile_id"] == selected_profile_id)
    new_name = st.sidebar.text_input("New profile name", value=current_name, key="rename_input")
    if st.sidebar.button("Rename", key="rename_confirm"):
        if new_name.strip() and new_name != current_name:
            db_migration.rename_profile(conn, selected_profile_id, new_name)
            st.session_state.user_profiles = None
            st.session_state.show_rename_modal = False
            st.success("Profile renamed!")
            st.rerun()

liked_ids = get_profile_likes(selected_profile_id)
st.sidebar.metric("Movies Liked", len(liked_ids))

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

tab1, tab2, tab3, tab4 = st.tabs(["Search", "Similar", "My Likes", "Recommendations"])


with tab1:
    st.subheader("Search for Movies")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        query = st.text_input("Enter a search query", placeholder="Interstellar or space exploration")
    with col2:
        search_type = st.selectbox("Search scope", ["Movie or Theme", "Title Only", "Theme Only"])
    with col3:
        approach = st.selectbox("Retrieval method", ["Semantic", "Keyword (BM25)"])

    # Year range filter
    col_year1, col_year2, col_year3 = st.columns([1, 1, 1])
    with col_year1:
        min_year = st.number_input("From year", min_value=1900, max_value=2030, value=1900, key="min_year_search")
    with col_year2:
        max_year = st.number_input("To year", min_value=1900, max_value=2030, value=2030, key="max_year_search")
    with col_year3:
        st.empty()  # For alignment

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
                candidate_count = min(len(movies_df), max(n * 5, n + 25))
                distances, indices = faiss_index.search(query_emb.astype("float32").reshape(1, -1), candidate_count)

                candidates = []
                for pos, idx in enumerate(indices[0]):
                    if idx < 0 or idx >= len(movies_df):
                        continue
                    movie = movies_df.iloc[idx]
                    if movie["movieId"] in seen_movie_ids:
                        continue
                    candidates.append(
                        {
                            "movie": movie,
                            "relevance_score": float(distances[0][pos]),
                        }
                    )

                for candidate in rank_with_recency(candidates)[: max(0, n - len(results))]:
                    movie = candidate["movie"]
                    results.append(
                        {
                            "movieId": movie["movieId"],
                            "Title": movie["title"],
                            "Genres": movie.get("genres", "N/A"),
                            "Score": f"{candidate['adjusted_score']:.3f} adjusted",
                        }
                    )
                    seen_movie_ids.add(movie["movieId"])
                st.markdown("#### Semantic Search Results")
            else:
                scores = bm25.get_scores(query.lower().split())
                candidate_count = max(n * 5, n + 25)
                top_idx = [idx for idx in np.argsort(scores)[::-1] if scores[idx] > 0][:candidate_count]
                candidates = []
                for idx in top_idx:
                    movie = movies_df.iloc[idx]
                    if movie["movieId"] in seen_movie_ids:
                        continue
                    candidates.append(
                        {
                            "movie": movie,
                            "relevance_score": float(scores[idx]),
                        }
                    )

                for candidate in rank_with_recency(candidates)[: max(0, n - len(results))]:
                    movie = candidate["movie"]
                    results.append(
                        {
                            "movieId": movie["movieId"],
                            "Title": movie["title"],
                            "Genres": movie.get("genres", "N/A"),
                            "Score": f"{candidate['adjusted_score']:.3f} adjusted",
                        }
                    )
                    seen_movie_ids.add(movie["movieId"])
                st.markdown("#### Keyword Search Results")

        # Apply year filter to results
        filtered_results = filter_by_year(results, min_year, max_year)

        if filtered_results:
            st.markdown(f"#### Results ({len(filtered_results)} found, filtered by year {min_year}-{max_year})")
            for result in filtered_results[:n]:
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    display_movie_card(result["Title"], result["Genres"], result["Score"])
                with col_right:
                    if st.button("Add", key=f"add_{result['movieId']}"):
                        db_migration.add_movie_to_profile(conn, selected_profile_id, int(result["movieId"]))
                        st.session_state.invalidate_likes_cache = True
                        st.success(f"Added '{result['Title']}'")
                        st.rerun()
        elif results:
            st.warning(f"No results found in year range {min_year}-{max_year}. Found {len(results)} results overall.")
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
                    db_migration.add_movie_to_profile(conn, selected_profile_id, int(movie["movieId"]))
                    st.session_state.invalidate_likes_cache = True
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
                    db_migration.remove_movie_from_profile(conn, selected_profile_id, movie_id)
                    st.session_state.invalidate_likes_cache = True
                    st.success("Removed")
                    st.rerun()

        st.metric("Progress", f"{len(liked_ids)}/15 movies", delta="More likes can improve recommendations")

        if st.button("Clear All Likes"):
            db_migration.clear_profile_likes(conn, selected_profile_id)
            st.session_state.invalidate_likes_cache = True
            st.success("Cleared all likes")
            st.rerun()
    else:
        st.info("Use the Search tab to add movies you like.")


with tab4:
    col_tab1, col_tab2 = st.columns(2)

    with col_tab1:
        st.subheader("Personalized Recommendations")
        st.caption("Content-based taste vector from your likes")

        if len(liked_ids) == 0:
            st.info("Use the Search tab to find and like movies.")
        elif len(liked_ids) < 2:
            st.warning(f"Add {2 - len(liked_ids)} more movie(s) to see recommendations.")
        else:
            n = st.slider("Show", 5, 20, 10)

            # Use new recommendation function
            recs = recommendations.compute_single_profile_recommendations(
                conn, selected_profile_id, embeddings, faiss_index, movies_df, n_results=n * 2
            )

            if recs:
                st.markdown(f"#### Based on Your {len(liked_ids)} Likes")

                # Apply recency ranking
                candidates = [
                    {"movie": movies_df[movies_df["movieId"] == rec["movie_id"]].iloc[0], "relevance_score": rec["similarity_score"]}
                    for rec in recs
                ]
                ranked = rank_with_recency(candidates)[:n]

                for candidate in ranked:
                    movie = candidate["movie"]
                    col_left, col_right = st.columns([2, 1])
                    with col_left:
                        display_movie_card(movie["title"], movie.get("genres", "N/A"), f"{candidate['adjusted_score']:.3f} adjusted")
                    with col_right:
                        if st.button("Add", key=f"rec_{movie['movieId']}"):
                            db_migration.add_movie_to_profile(conn, selected_profile_id, int(movie["movieId"]))
                            st.session_state.invalidate_likes_cache = True
                            st.success(f"Added '{movie['title']}'")
                            st.rerun()
            else:
                st.error("Could not generate recommendations from the saved likes.")

    with col_tab2:
        st.subheader("Group Recommendations")
        st.caption("Find movies for multiple profiles")

        enable_collab = st.checkbox("Enable group watch mode", value=False, key="enable_collab_main")

        if enable_collab:
            collab_profiles = st.multiselect(
                "Select profiles",
                options=[p["profile_id"] for p in user_profiles],
                format_func=lambda pid: next(p["profile_name"] for p in user_profiles if p["profile_id"] == pid),
                key="collab_profiles_main",
            )

            if len(collab_profiles) >= 2:
                st.markdown(f"### Movies for {len(collab_profiles)} profiles")

                variance_penalty = st.slider(
                    "Consensus strength",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    help="Higher = stricter consensus. 0.0 = try anything, 1.0 = everyone must agree.",
                    key="variance_penalty_main",
                )

                n_collab = st.slider("Show group recommendations", 5, 20, 10, key="n_collab_main")

                # Compute collaborative recommendations
                collab_recs = recommendations.compute_collaborative_recommendations(
                    conn,
                    collab_profiles,
                    embeddings,
                    faiss_index,
                    movies_df,
                    variance_penalty=variance_penalty,
                    n_results=n_collab,
                )

                if collab_recs:
                    st.markdown(f"#### {len(collab_recs)} Results")
                    for rec in collab_recs:
                        col_left, col_right = st.columns([2, 1])

                        with col_left:
                            movie_row = movies_df[movies_df["movieId"] == rec["movie_id"]]
                            if len(movie_row) > 0:
                                movie = movie_row.iloc[0]
                                score_text = f"Consensus: {rec['combined_score']:.3f} | Mean: {rec['mean_similarity']:.3f}"
                                display_movie_card(movie["title"], movie.get("genres", "N/A"), score_text)

                                # Show per-profile appeal
                                with st.expander("Profile details"):
                                    for pid, score in rec["profile_scores"].items():
                                        pname = next(p["profile_name"] for p in user_profiles if p["profile_id"] == pid)
                                        st.write(f"**{pname}**: {score:.3f}")
                                    st.caption(f"Variance: {rec['variance']:.4f} (lower = more consensus)")

                        with col_right:
                            if st.button("Add to profiles", key=f"collab_rec_{rec['movie_id']}"):
                                for pid in collab_profiles:
                                    db_migration.add_movie_to_profile(conn, pid, rec["movie_id"])
                                st.session_state.invalidate_likes_cache = True
                                st.success(f"Added to {len(collab_profiles)} profiles!")
                                st.rerun()
                else:
                    st.warning("No group recommendations found. Try adjusting the consensus slider.")
            else:
                st.info("Select 2+ profiles to see group recommendations.")


st.markdown("---")
st.markdown(
    """**How it works**

- Search compares semantic embeddings with BM25 keyword matching.
- Similar movies come from the FAISS embedding index.
- Likes are stored locally in SQLite.
- Search and recommendations apply a moderate newer-movie boost when relevance is close.
- Recommendations in the app use a content-based user vector; Phase 4 explores collaborative filtering as a notebook experiment.
"""
)
