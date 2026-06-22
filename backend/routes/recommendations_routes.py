"""Recommendation endpoints for single-profile and collaborative modes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import recommendations
from main import app_state

router = APIRouter()


class RecommendationResult(BaseModel):
    movie_id: int
    title: str
    genres: str
    similarity_score: Optional[float] = None


class CollaborativeRecommendationResult(BaseModel):
    movie_id: int
    title: str
    genres: str
    combined_score: float
    mean_similarity: float
    variance: float
    profile_scores: Dict[str, float]


class SingleProfileRequest(BaseModel):
    profile_id: str
    limit: int = 10


class CollaborativeRequest(BaseModel):
    profile_ids: List[str]
    variance_penalty: float = 0.3
    limit: int = 10


@router.post("/single-profile")
async def get_single_profile_recommendations(payload: SingleProfileRequest) -> dict:
    """Get personalized recommendations for a single profile."""
    try:
        recs = recommendations.compute_single_profile_recommendations(
            app_state.conn,
            payload.profile_id,
            app_state.embeddings,
            app_state.faiss_index,
            app_state.movies_df,
            n_results=payload.limit
        )

        results = []
        for rec in recs:
            movie = app_state.movies_df[app_state.movies_df["movieId"] == rec["movie_id"]]
            if len(movie) > 0:
                results.append({
                    "movie_id": rec["movie_id"],
                    "title": movie.iloc[0]["title"],
                    "genres": movie.iloc[0].get("genres", ""),
                    "similarity_score": rec["similarity_score"]
                })

        return {
            "profile_id": payload.profile_id,
            "recommendations": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaborative")
async def get_collaborative_recommendations(payload: CollaborativeRequest) -> dict:
    """Get collaborative recommendations for multiple profiles."""
    try:
        if len(payload.profile_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 profiles required for collaborative recommendations")

        recs = recommendations.compute_collaborative_recommendations(
            app_state.conn,
            payload.profile_ids,
            app_state.embeddings,
            app_state.faiss_index,
            app_state.movies_df,
            variance_penalty=payload.variance_penalty,
            n_results=payload.limit
        )

        results = []
        for rec in recs:
            movie = app_state.movies_df[app_state.movies_df["movieId"] == rec["movie_id"]]
            if len(movie) > 0:
                results.append({
                    "movie_id": rec["movie_id"],
                    "title": movie.iloc[0]["title"],
                    "genres": movie.iloc[0].get("genres", ""),
                    "combined_score": rec["combined_score"],
                    "mean_similarity": rec["mean_similarity"],
                    "variance": rec["variance"],
                    "profile_scores": rec["profile_scores"]
                })

        return {
            "profile_ids": payload.profile_ids,
            "variance_penalty": payload.variance_penalty,
            "recommendations": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
