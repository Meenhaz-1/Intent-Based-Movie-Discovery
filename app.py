import streamlit as st
import pandas as pd
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import sqlite3
from datetime import datetime
import tmdb_helper
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup
CHECKPOINTS_DIR = Path('checkpoints')
RESULTS_DIR = Path('results')

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

st.title("🎬 Movie Recommendation System")
st.markdown("**Find movies you'll love** using content-based & collaborative filtering")

# Load data
@st.cache_resource
def load_artifacts():
    # Load embeddings and index
    embeddings = np.load(CHECKPOINTS_DIR / 'embeddings.npy')
    faiss_index = faiss.read_index(str(CHECKPOINTS_DIR / 'faiss_index.bin'))
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    # Load MovieLens (authoritative source)
    movie_ids_df = pd.read_csv(CHECKPOINTS_DIR / 'movie_ids.csv')
    movies_df = pd.read_csv(Path('data/movielens/movies.csv'))
    tags_df = pd.read_csv(Path('data/movielens/tags.csv'))

    # Merge to get genres
    movie_ids_df = movie_ids_df.merge(movies_df[['movieId', 'genres']], on='movieId', how='left')
    movie_ids_df['genres'] = movie_ids_df['genres'].fillna('')

    # Build combined text for BM25
    tags_by_movie = tags_df.dropna(subset=['tag']).groupby('movieId')['tag'].apply(' '.join).to_dict()
    combined_text = {}
    for idx, row in movie_ids_df.iterrows():
        mid = row['movieId']
        genres = row.get('genres', '')
        tags = tags_by_movie.get(mid, '')
        combined_text[mid] = f"{genres} {tags}".strip()

    # BM25 index
    corpus = [combined_text.get(mid, '') for mid in movie_ids_df['movieId']]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    return {
        'embeddings': embeddings,
        'faiss_index': faiss_index,
        'embedding_model': embedding_model,
        'movies_df': movie_ids_df,  # Use merged version
        'bm25': bm25,
    }

artifacts = load_artifacts()
embeddings = artifacts['embeddings']
faiss_index = artifacts['faiss_index']
embedding_model = artifacts['embedding_model']
movies_df = artifacts['movies_df']
bm25 = artifacts['bm25']

# Initialize user store
def init_user_store():
    conn = sqlite3.connect(CHECKPOINTS_DIR / 'user_preferences.sqlite')
    conn.execute('''CREATE TABLE IF NOT EXISTS user_likes (
        user_id TEXT, movie_id INTEGER, liked_at TIMESTAMP, review_text TEXT,
        PRIMARY KEY (user_id, movie_id))''')
    conn.commit()
    return conn

conn = init_user_store()

# Helper to display movie card with TMDB data
def display_movie_card(title, genres, score, is_similar=False):
    """Display a movie with poster and details if available."""
    col1, col2 = st.columns([1, 3])

    with col1:
        movie_info = tmdb_helper.fetch_movie_info(title)
        if movie_info and movie_info.get('poster_url'):
            st.image(movie_info['poster_url'], width=150)
        else:
            st.write("📽️ No poster")

    with col2:
        st.markdown(f"**{title}**")
        st.caption(genres if genres else "N/A")

        if movie_info:
            st.markdown(f"⭐ {movie_info.get('rating', 0):.1f} ({movie_info.get('vote_count', 0)} votes)")
            st.caption(f"📅 {movie_info.get('release_date', 'Unknown')}")

            if movie_info.get('plot'):
                st.write(f"📝 {movie_info['plot'][:200]}...")

            if movie_info.get('cast'):
                st.caption(f"👥 Cast: {', '.join(movie_info['cast'][:3])}")

        st.markdown(f"**Score**: {score}")

    st.divider()

# Sidebar
st.sidebar.markdown("### 🎯 User Profile")
user_id = st.sidebar.text_input("Your ID", value="demo_user")

# TMDB API Key (from .env or manual input)
st.sidebar.markdown("### 📺 TMDB Setup")
tmdb_key_env = os.getenv('TMDB_API_KEY', '').strip()

if tmdb_key_env:
    tmdb_helper.set_api_key(tmdb_key_env)
    st.sidebar.success("✓ TMDB connected (from .env)")
else:
    tmdb_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="Get from themoviedb.org")
    if tmdb_key:
        tmdb_helper.set_api_key(tmdb_key)
        st.sidebar.success("✓ TMDB connected")
    else:
        st.sidebar.info("💡 Add TMDB_API_KEY to .env or enter above to see posters")

def get_user_likes(user_id):
    df = pd.read_sql_query('SELECT movie_id FROM user_likes WHERE user_id = ?', conn, params=(user_id,))
    return df['movie_id'].tolist() if len(df) > 0 else []

liked_ids = get_user_likes(user_id)
st.sidebar.metric("Movies Liked", len(liked_ids))

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "📊 Similar", "❤️ My Likes", "🎯 Recommendations"])

# TAB 1: Search
with tab1:
    st.subheader("Search for Movies")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query = st.text_input("Enter a search query", placeholder="e.g., 'Interstellar' or 'space exploration'")
    with col2:
        search_type = st.selectbox("Find", ["Movie or Theme", "Title Only", "Theme Only"], label_visibility="collapsed")
    with col3:
        approach = st.selectbox("Method", ["Semantic", "Keyword (BM25)"], label_visibility="collapsed")

    if query:
        n = st.slider("Results", 5, 20, 10)
        results = []

        # Title matching
        if search_type in ["Movie or Theme", "Title Only"]:
            title_matches = movies_df[movies_df['title'].str.lower().str.contains(query.lower(), na=False)].head(1)
            for _, row in title_matches.iterrows():
                results.append({'Rank': len(results)+1, 'Title': row['title'], 'Genres': row.get('genres', 'N/A'), 'Score': '★ Exact'})

        # Thematic search
        if search_type in ["Movie or Theme", "Theme Only"]:
            if approach == "Semantic":
                query_emb = embedding_model.encode(query, convert_to_numpy=True)
                query_emb = query_emb / np.linalg.norm(query_emb)
                distances, indices = faiss_index.search(query_emb.astype('float32').reshape(1, -1), n + 5)

                for idx in indices[0]:
                    movie = movies_df.iloc[idx]
                    if not any(r['Title'] == movie['title'] for r in results):
                        results.append({'Rank': len(results)+1, 'Title': movie['title'], 'Genres': movie.get('genres', 'N/A'), 'Score': f"{distances[0][list(indices[0]).index(idx)]:.3f}"})
                        if len(results) >= n:
                            break
                st.markdown("#### Semantic Search Results")
            else:
                scores = bm25.get_scores(query.lower().split())
                top_idx = np.argsort(scores)[::-1]
                for idx in top_idx:
                    movie = movies_df.iloc[idx]
                    if not any(r['Title'] == movie['title'] for r in results):
                        results.append({'Rank': len(results)+1, 'Title': movie['title'], 'Genres': movie.get('genres', 'N/A'), 'Score': f"{scores[idx]:.3f}" if scores[idx] > 0 else "0.000"})
                        if len(results) >= n:
                            break
                st.markdown("#### Keyword Search Results")

        if results:
            st.markdown("#### Results")
            for result in results[:n]:
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    display_movie_card(result['Title'], result['Genres'], result['Score'])
                with col_right:
                    if st.button("❤️ Add", key=f"add_{result['Title']}"):
                        movie_id = movies_df[movies_df['title'] == result['Title']]['movieId'].values
                        if len(movie_id) > 0:
                            conn.execute('INSERT OR REPLACE INTO user_likes (user_id, movie_id, liked_at) VALUES (?, ?, ?)',
                                       (user_id, int(movie_id[0]), datetime.now()))
                            conn.commit()
                            st.success(f"Added '{result['Title']}'!")
                            st.rerun()
        else:
            st.warning("No results found.")

# TAB 2: Similar
with tab2:
    st.subheader("Find Similar Movies")
    selected_movie = st.selectbox("Pick a movie", movies_df['title'].values)

    if selected_movie:
        movie_idx = movies_df[movies_df['title'] == selected_movie].index[0]
        n = st.slider("Count", 5, 20, 10)

        movie_emb = embeddings[movie_idx].astype('float32').reshape(1, -1)
        distances, indices = faiss_index.search(movie_emb, n + 1)

        st.markdown("#### Similar Movies")
        for rank, idx in enumerate(indices[0][1:]):
            if rank >= n:
                break
            movie = movies_df.iloc[idx]
            col_left, col_right = st.columns([2, 1])
            with col_left:
                display_movie_card(movie['title'], movie.get('genres', 'N/A'), f"{distances[0][rank+1]:.3f}")
            with col_right:
                if st.button("❤️ Like", key=f"like_{movie['movieId']}"):
                    conn.execute('INSERT OR REPLACE INTO user_likes (user_id, movie_id, liked_at) VALUES (?, ?, ?)',
                               (user_id, int(movie['movieId']), datetime.now()))
                    conn.commit()
                    st.success(f"Added '{movie['title']}'!")
                    st.rerun()

# TAB 3: My Likes
with tab3:
    st.subheader("Your Liked Movies")

    if liked_ids:
        st.markdown(f"#### Your {len(liked_ids)} Liked Movies")
        for mid in liked_ids:
            movie = movies_df[movies_df['movieId'] == mid]
            if len(movie) > 0:
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    display_movie_card(movie.iloc[0]['title'], movie.iloc[0].get('genres', 'N/A'), f"#{liked_ids.index(mid)+1}")
                with col_right:
                    if st.button("🗑️ Remove", key=f"remove_{mid}"):
                        conn.execute('DELETE FROM user_likes WHERE user_id = ? AND movie_id = ?', (user_id, mid))
                        conn.commit()
                        st.success("Removed!")
                        st.rerun()

        st.metric("Progress", f"{len(liked_ids)}/15 movies", delta="More data → Better recommendations")

        if st.button("Clear All Likes"):
            conn.execute('DELETE FROM user_likes WHERE user_id = ?', (user_id,))
            conn.commit()
            st.success("Cleared all likes!")
            st.rerun()
    else:
        st.info("👈 Use the Search tab to add movies you like!")

# TAB 4: Recommendations
with tab4:
    st.subheader("Personalized Recommendations")

    if len(liked_ids) == 0:
        st.info("👈 **Use the Search tab** to find and like movies!")
    elif len(liked_ids) < 2:
        st.warning(f"⏳ Add {2 - len(liked_ids)} more movie(s) to see recommendations")
    else:
        n = st.slider("Show", 5, 20, 10)

        # Build user vector
        indices_list = []
        for mid in liked_ids:
            idx = movies_df[movies_df['movieId'] == mid].index
            if len(idx) > 0:
                indices_list.append(idx[0])

        if indices_list:
            user_emb = embeddings[indices_list].mean(axis=0)
            user_emb = user_emb / np.linalg.norm(user_emb)
            distances, indices = faiss_index.search(user_emb.astype('float32').reshape(1, -1), n + len(liked_ids))

            st.markdown(f"#### Based on Your {len(liked_ids)} Likes")
            rec_count = 0
            for idx in indices[0]:
                if rec_count >= n:
                    break
                movie = movies_df.iloc[idx]
                if movie['movieId'] not in liked_ids:
                    score = f"{distances[0][list(indices[0]).index(idx)]:.3f}"
                    col_left, col_right = st.columns([2, 1])
                    with col_left:
                        display_movie_card(movie['title'], movie.get('genres', 'N/A'), score)
                    with col_right:
                        if st.button("❤️ Add", key=f"rec_{movie['movieId']}"):
                            conn.execute('INSERT OR REPLACE INTO user_likes (user_id, movie_id, liked_at) VALUES (?, ?, ?)',
                                       (user_id, int(movie['movieId']), datetime.now()))
                            conn.commit()
                            st.success(f"Added '{movie['title']}'!")
                            st.rerun()
                    rec_count += 1
        else:
            st.error("Could not generate recommendations")

st.markdown("---")
st.markdown("""**How it works:**
- **Search**: Find movies via semantic similarity or keyword matching
- **Similar**: Discover movies like your favorites using embeddings
- **My Likes**: Track your profile
- **Recommendations**: Get personalized picks (content-based 0-10 likes, blended 10+ likes)""")
