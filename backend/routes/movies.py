"""Movie likes management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

import db_migration
from main import app_state

router = APIRouter()


class MovieLike(BaseModel):
    profile_id: str
    movie_id: int
    rating: Optional[float] = None


class MovieResponse(BaseModel):
    movie_id: int
    title: str
    genres: str


@router.get("/{profile_id}/likes")
async def get_profile_likes(profile_id: str) -> List[int]:
    """Get all liked movie IDs for a profile."""
    try:
        return db_migration.get_profile_likes(app_state.conn, profile_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{profile_id}/likes")
async def add_movie_to_profile(payload: MovieLike) -> dict:
    """Add a movie to a profile's likes."""
    try:
        db_migration.add_movie_to_profile(
            app_state.conn,
            payload.profile_id,
            payload.movie_id,
            rating=payload.rating
        )
        movie = app_state.movies_df[app_state.movies_df["movieId"] == payload.movie_id]
        movie_title = movie.iloc[0]["title"] if len(movie) > 0 else f"Movie {payload.movie_id}"
        return {"message": f"Added '{movie_title}' to likes"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{profile_id}/likes/{movie_id}")
async def remove_movie_from_profile(profile_id: str, movie_id: int) -> dict:
    """Remove a movie from a profile's likes."""
    try:
        db_migration.remove_movie_from_profile(app_state.conn, profile_id, movie_id)
        return {"message": f"Removed movie {movie_id} from likes"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{profile_id}/likes")
async def clear_profile_likes(profile_id: str) -> dict:
    """Clear all likes from a profile."""
    try:
        db_migration.clear_profile_likes(app_state.conn, profile_id)
        return {"message": "Cleared all likes"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/{query}")
async def search_movies(query: str, limit: int = 20) -> List[MovieResponse]:
    """Search for movies by title or keywords."""
    try:
        results = []
        # Title search
        title_matches = app_state.movies_df[
            app_state.movies_df["title"].str.lower().str.contains(query.lower(), regex=False, na=False)
        ].head(5)

        seen_ids = set()
        for _, row in title_matches.iterrows():
            movie_id = int(row["movieId"])
            seen_ids.add(movie_id)
            results.append(MovieResponse(
                movie_id=movie_id,
                title=row["title"],
                genres=row.get("genres", "")
            ))

        # Keyword search
        scores = app_state.bm25.get_scores(query.lower().split())
        top_idx = [idx for idx in range(len(scores)) if scores[idx] > 0]
        top_idx = sorted(top_idx, key=lambda i: scores[i], reverse=True)

        for idx in top_idx[:limit - len(results)]:
            row = app_state.movies_df.iloc[idx]
            movie_id = int(row["movieId"])
            if movie_id not in seen_ids:
                seen_ids.add(movie_id)
                results.append(MovieResponse(
                    movie_id=movie_id,
                    title=row["title"],
                    genres=row.get("genres", "")
                ))

        return results[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
