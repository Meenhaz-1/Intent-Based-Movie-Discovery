"""FastAPI backend for Movie Recommendations with Multi-Profile Support."""

import os
from pathlib import Path
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
import faiss
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

import db_migration
import recommendations
import tmdb_helper

load_dotenv()

# Paths
CHECKPOINTS_DIR = Path("../checkpoints")
MOVIELENS_DIR = Path("../data/movielens")
DB_PATH = CHECKPOINTS_DIR / "user_preferences.sqlite"

# Constants
RECENCY_HALF_LIFE_YEARS = 20
RECENCY_WEIGHT = 0.20
RELEVANCE_WEIGHT = 0.80


class AppState:
    """Global application state."""

    def __init__(self):
        self.embeddings = None
        self.faiss_index = None
        self.embedding_model = None
        self.movies_df = None
        self.bm25 = None
        self.conn = None


app_state = AppState()


def load_artifacts():
    """Load embeddings, FAISS index, and movie data (called once on startup)."""
    print("Loading artifacts...")

    # Load embeddings and FAISS index
    app_state.embeddings = np.load(CHECKPOINTS_DIR / "embeddings.npy")
    app_state.faiss_index = faiss.read_index(str(CHECKPOINTS_DIR / "faiss_index.bin"))
    app_state.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Load movies
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

    app_state.movies_df = movie_ids_df
    app_state.bm25 = BM25Okapi(tokenized_corpus)

    # Initialize database
    app_state.conn = db_migration.init_database(DB_PATH)

    # Setup TMDB if available
    tmdb_key = os.getenv("TMDB_API_KEY", "").strip()
    if tmdb_key:
        tmdb_helper.set_api_key(tmdb_key)

    print("Artifacts loaded successfully!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    load_artifacts()
    yield
    # Shutdown
    if app_state.conn:
        app_state.conn.close()


# Create FastAPI app with CORS enabled
app = FastAPI(
    title="Movie Recommendations API",
    description="FastAPI backend for multi-profile movie recommendations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost:3000", "127.0.0.1:3000", "*"],  # React dev server + production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import route handlers
from routes import profiles, movies, search, recommendations_routes


# Include routers
app.include_router(profiles.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(movies.router, prefix="/api/movies", tags=["Movies"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(recommendations_routes.router, prefix="/api/recommendations", tags=["Recommendations"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Movie Recommendations API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check for load balancer."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
