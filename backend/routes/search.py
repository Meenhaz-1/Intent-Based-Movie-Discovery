"""Advanced search endpoints with semantic and keyword search."""

import re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import numpy as np
from main import app_state

router = APIRouter()


class SearchResult(BaseModel):
    movie_id: int
    title: str
    genres: str
    score: float


class SearchQuery(BaseModel):
    query: str
    method: str = "semantic"  # "semantic" or "keyword"
    limit: int = 10


def extract_release_year(title: str) -> Optional[int]:
    """Extract year from movie title like 'Movie Name (1999)'."""
    match = re.search(r"\((\d{4})\)\s*$", title)
    return int(match.group(1)) if match else None


def extract_year_constraints_from_query(query: str) -> Optional[tuple]:
    """Extract year constraints from natural language query."""
    current_year = datetime.now().year
    min_year = 1900
    max_year = current_year

    # "from YYYY" or "since YYYY"
    from_match = re.search(r'\b(?:from|since)\s+(\d{4})\b', query, re.IGNORECASE)
    if from_match:
        min_year = int(from_match.group(1))
        return (min_year, max_year)

    # "YYYY onwards"
    onwards_match = re.search(r'\b(\d{4})\s+onwards?\b', query, re.IGNORECASE)
    if onwards_match:
        min_year = int(onwards_match.group(1))
        return (min_year, max_year)

    # "after YYYY"
    after_match = re.search(r'\bafter\s+(\d{4})\b', query, re.IGNORECASE)
    if after_match:
        min_year = int(after_match.group(1))
        return (min_year, max_year)

    # "before YYYY"
    before_match = re.search(r'\bbefore\s+(\d{4})\b', query, re.IGNORECASE)
    if before_match:
        max_year = int(before_match.group(1))
        return (min_year, max_year)

    # "YYYY-YYYY"
    range_match = re.search(r'\b(\d{4})\s*-\s*(\d{4})\b', query)
    if range_match:
        min_year = int(range_match.group(1))
        max_year = int(range_match.group(2))
        return (min_year, max_year)

    return None


def filter_by_year(results: List[dict], min_year: int, max_year: int) -> List[dict]:
    """Filter results by release year."""
    filtered = []
    for result in results:
        year = extract_release_year(result["title"])
        if year and min_year <= year <= max_year:
            filtered.append(result)
    return filtered


@router.post("/semantic")
async def semantic_search(payload: SearchQuery) -> dict:
    """Perform semantic search using embeddings."""
    try:
        query = payload.query
        limit = payload.limit

        # Extract year constraints
        year_range = extract_year_constraints_from_query(query)
        if year_range:
            min_year, max_year = year_range
        else:
            min_year, max_year = 1900, datetime.now().year

        # Check for exact title matches first
        query_lower = query.lower().strip()
        exact_match_ids = set()
        exact_matches = []
        for idx, movie in app_state.movies_df.iterrows():
            title_lower = movie["title"].lower()
            if query_lower in title_lower or title_lower in query_lower:
                movie_id = int(movie["movieId"])
                exact_match_ids.add(movie_id)
                exact_matches.append({
                    "movie_id": movie_id,
                    "title": movie["title"],
                    "genres": movie.get("genres", ""),
                    "score": 1.0  # Perfect score for exact matches
                })

        # Filter exact matches by year
        filtered_exact = filter_by_year(exact_matches, min_year, max_year)

        # Encode query
        query_emb = app_state.embedding_model.encode(query, convert_to_numpy=True)
        query_emb = query_emb / np.linalg.norm(query_emb)

        # Search
        candidate_count = min(len(app_state.movies_df), max(limit * 5, limit + 25))
        distances, indices = app_state.faiss_index.search(
            query_emb.astype("float32").reshape(1, -1),
            candidate_count
        )

        semantic_results = []
        for pos, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(app_state.movies_df):
                continue

            movie = app_state.movies_df.iloc[idx]
            movie_id = int(movie["movieId"])
            # Skip exact matches to avoid duplicates
            if movie_id not in exact_match_ids:
                semantic_results.append({
                    "movie_id": movie_id,
                    "title": movie["title"],
                    "genres": movie.get("genres", ""),
                    "score": float(distances[0][pos])
                })

        # Filter semantic results by year
        filtered_semantic = filter_by_year(semantic_results, min_year, max_year)

        # Combine: exact matches first, then semantic results
        combined_results = filtered_exact + filtered_semantic
        filtered_results = combined_results

        return {
            "query": query,
            "year_range": year_range,
            "results": filtered_results[:limit],
            "total": len(filtered_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keyword")
async def keyword_search(payload: SearchQuery) -> dict:
    """Perform keyword search using BM25."""
    try:
        query = payload.query
        limit = payload.limit

        # Extract year constraints
        year_range = extract_year_constraints_from_query(query)

        # Year constraints
        if year_range:
            min_year, max_year = year_range
        else:
            min_year, max_year = 1900, datetime.now().year

        # Check for exact title matches first
        query_lower = query.lower().strip()
        exact_match_ids = set()
        exact_matches = []
        for idx, movie in app_state.movies_df.iterrows():
            title_lower = movie["title"].lower()
            if query_lower in title_lower or title_lower in query_lower:
                movie_id = int(movie["movieId"])
                exact_match_ids.add(movie_id)
                exact_matches.append({
                    "movie_id": movie_id,
                    "title": movie["title"],
                    "genres": movie.get("genres", ""),
                    "score": 100.0  # High score for exact matches
                })

        # Filter exact matches by year
        filtered_exact = filter_by_year(exact_matches, min_year, max_year)

        # Perform BM25 search for other results
        scores = app_state.bm25.get_scores(query.lower().split())
        candidate_count = max(limit * 5, limit + 25)
        top_idx = [idx for idx in range(len(scores)) if scores[idx] > 0]
        top_idx = sorted(top_idx, key=lambda i: scores[i], reverse=True)[:candidate_count]

        other_results = []
        for idx in top_idx:
            movie = app_state.movies_df.iloc[idx]
            movie_id = int(movie["movieId"])
            # Skip exact matches to avoid duplicates
            if movie_id not in exact_match_ids:
                other_results.append({
                    "movie_id": movie_id,
                    "title": movie["title"],
                    "genres": movie.get("genres", ""),
                    "score": float(scores[idx])
                })

        # Filter other results by year
        filtered_other = filter_by_year(other_results, min_year, max_year)

        # Combine: exact matches first, then other results
        combined_results = filtered_exact + filtered_other
        filtered_results = combined_results

        return {
            "query": query,
            "year_range": year_range,
            "results": filtered_results[:limit],
            "total": len(filtered_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{movie_id}")
async def find_similar_movies(movie_id: int, limit: int = 10) -> dict:
    """Find movies similar to a given movie."""
    try:
        movie = app_state.movies_df[app_state.movies_df["movieId"] == movie_id]
        if len(movie) == 0:
            raise HTTPException(status_code=404, detail=f"Movie {movie_id} not found")

        movie_idx = movie.index[0]
        movie_emb = app_state.embeddings[movie_idx].astype("float32").reshape(1, -1)
        distances, indices = app_state.faiss_index.search(movie_emb, limit + 1)

        results = []
        for rank, idx in enumerate(indices[0][1:]):  # Skip first (itself)
            if rank >= limit:
                break
            if idx < 0 or idx >= len(app_state.movies_df):
                continue

            similar_movie = app_state.movies_df.iloc[idx]
            results.append({
                "movie_id": int(similar_movie["movieId"]),
                "title": similar_movie["title"],
                "genres": similar_movie.get("genres", ""),
                "score": float(distances[0][rank + 1])
            })

        return {
            "source_movie_id": movie_id,
            "similar_movies": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
