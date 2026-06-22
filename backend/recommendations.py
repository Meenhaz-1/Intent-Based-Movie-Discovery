"""Recommendation algorithms for individual profiles and collaborative groups."""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

import db_migration


def compute_profile_taste_vector(
    conn: sqlite3.Connection,
    profile_id: str,
    embeddings: np.ndarray,
    movies_df: pd.DataFrame,
    use_recency_weighting: bool = False,
) -> Optional[np.ndarray]:
    """
    Compute a normalized taste vector for a single profile.

    The taste vector is the mean embedding of all liked movies, normalized to unit length.

    Args:
        conn: Database connection
        profile_id: Profile ID
        embeddings: Full embedding matrix (N x embedding_dim)
        movies_df: Movies dataframe with movieId column
        use_recency_weighting: If True, weight recent likes more heavily

    Returns:
        Normalized taste vector of shape (embedding_dim,) or None if profile has no likes
    """
    liked_ids = db_migration.get_profile_likes(conn, profile_id)

    if not liked_ids:
        return None

    # Find indices in embeddings array for each liked movie
    indices_list = []
    for movie_id in liked_ids:
        idx_results = movies_df[movies_df["movieId"] == movie_id].index
        if len(idx_results) > 0:
            indices_list.append(idx_results[0])

    if not indices_list:
        return None

    # Compute mean embedding with optional recency weighting
    if use_recency_weighting:
        # Older likes get lower weight; newer likes get higher weight
        # Weights are 0.5 to 1.5 range based on like order (oldest to newest)
        n_likes = len(liked_ids)
        weights = np.linspace(0.5, 1.5, n_likes)
        weighted_emb = np.average(embeddings[indices_list], axis=0, weights=weights)
    else:
        weighted_emb = embeddings[indices_list].mean(axis=0)

    # Normalize to unit length
    norm = np.linalg.norm(weighted_emb)
    if norm == 0:
        return None

    return weighted_emb / norm


def compute_collaborative_recommendations(
    conn: sqlite3.Connection,
    selected_profile_ids: List[str],
    embeddings: np.ndarray,
    faiss_index: Any,
    movies_df: pd.DataFrame,
    variance_penalty: float = 0.3,
    n_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Compute collaborative recommendations for multiple profiles.

    Finds movies that appeal to all selected profiles by:
    1. Computing taste vector for each profile
    2. Averaging taste vectors (consensus vector)
    3. Scoring candidates by mean similarity and variance penalty
    4. Returning top N by consensus score

    Args:
        conn: Database connection
        selected_profile_ids: List of profile IDs to include
        embeddings: Full embedding matrix (N x embedding_dim)
        faiss_index: FAISS index for semantic search
        movies_df: Movies dataframe with movieId, title, genres columns
        variance_penalty: Penalty coefficient for outliers (0.0-1.0)
            - 0.0: No penalty, pure mean-based ranking
            - 0.3: Default, moderate consensus emphasis
            - 0.7: Strong consensus emphasis (only movies everyone likes)
            - 1.0: Extreme (only perfect consensus)
        n_results: Number of recommendations to return

    Returns:
        List of dicts with keys:
        {
            "movie_id": int,
            "title": str,
            "genres": str,
            "combined_score": float,  # Main ranking score
            "mean_similarity": float,  # Average similarity across profiles
            "variance": float,  # Variance of similarities (lower = more consensus)
            "profile_scores": dict,  # Per-profile similarity scores
        }
    """
    # Step 1: Compute taste vectors for each selected profile
    taste_vectors = {}
    profile_name_map = {}  # For debug/display

    for profile_id in selected_profile_ids:
        vec = compute_profile_taste_vector(conn, profile_id, embeddings, movies_df)
        if vec is not None:
            taste_vectors[profile_id] = vec

            # Get profile name for reference
            cursor = conn.cursor()
            cursor.execute("SELECT profile_name FROM profiles WHERE profile_id = ?", (profile_id,))
            result = cursor.fetchone()
            profile_name_map[profile_id] = result[0] if result else profile_id

    if not taste_vectors:
        # No profiles have likes; return empty
        return []

    # Step 2: Compute weighted average of taste vectors (simple average for now)
    combined_vec = np.mean(list(taste_vectors.values()), axis=0)
    combined_vec_norm = np.linalg.norm(combined_vec)
    if combined_vec_norm == 0:
        return []

    combined_vec = combined_vec / combined_vec_norm

    # Step 3: Retrieve candidates from FAISS
    candidate_count = min(len(movies_df), max(n_results * 8, n_results + len(selected_profile_ids) * 10))
    distances, indices = faiss_index.search(combined_vec.astype("float32").reshape(1, -1), candidate_count)

    # Step 4: Score candidates
    candidates = []
    all_liked_ids = set()
    for profile_id in selected_profile_ids:
        all_liked_ids.update(db_migration.get_profile_likes(conn, profile_id))

    for pos, idx in enumerate(indices[0]):
        if idx < 0 or idx >= len(movies_df):
            continue

        movie = movies_df.iloc[idx]
        movie_id = int(movie["movieId"])

        # Skip already-liked movies
        if movie_id in all_liked_ids:
            continue

        # Compute similarity to combined vector for this movie
        movie_emb = embeddings[idx]
        movie_emb_norm = np.linalg.norm(movie_emb)
        if movie_emb_norm == 0:
            continue

        movie_emb_normalized = movie_emb / movie_emb_norm

        # Score this movie across all profiles
        profile_scores = {}
        individual_similarities = []

        for profile_id, taste_vec in taste_vectors.items():
            similarity = float(np.dot(movie_emb_normalized, taste_vec))
            profile_scores[profile_id] = similarity
            individual_similarities.append(similarity)

        # Compute consensus score
        mean_similarity = float(np.mean(individual_similarities))
        variance = float(np.var(individual_similarities))

        # Apply variance penalty: penalize high variance (disagreement)
        consensus_score = mean_similarity * (1.0 - variance_penalty * min(variance, 1.0))

        candidates.append(
            {
                "movie_id": movie_id,
                "title": movie["title"],
                "genres": movie.get("genres", ""),
                "combined_score": consensus_score,
                "mean_similarity": mean_similarity,
                "variance": variance,
                "profile_scores": profile_scores,
                "distance_to_combined": float(distances[0][pos]),
            }
        )

    # Step 5: Rank by combined score and return top N
    candidates = sorted(candidates, key=lambda c: c["combined_score"], reverse=True)
    return candidates[:n_results]


def compute_single_profile_recommendations(
    conn: sqlite3.Connection,
    profile_id: str,
    embeddings: np.ndarray,
    faiss_index: Any,
    movies_df: pd.DataFrame,
    n_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Compute recommendations for a single profile (existing functionality).

    Args:
        conn: Database connection
        profile_id: Profile ID
        embeddings: Full embedding matrix (N x embedding_dim)
        faiss_index: FAISS index for semantic search
        movies_df: Movies dataframe with movieId, title, genres columns
        n_results: Number of recommendations to return

    Returns:
        List of dicts with keys:
        {
            "movie_id": int,
            "title": str,
            "genres": str,
            "similarity_score": float,
        }
    """
    # Compute profile taste vector
    taste_vec = compute_profile_taste_vector(conn, profile_id, embeddings, movies_df)
    if taste_vec is None:
        return []

    # Get liked movies to exclude
    liked_ids = set(db_migration.get_profile_likes(conn, profile_id))

    # Retrieve candidates from FAISS
    candidate_count = min(len(movies_df), max(n_results * 8, n_results + 50))
    distances, indices = faiss_index.search(taste_vec.astype("float32").reshape(1, -1), candidate_count)

    # Build result list
    results = []
    for pos, idx in enumerate(indices[0]):
        if idx < 0 or idx >= len(movies_df):
            continue

        movie = movies_df.iloc[idx]
        movie_id = int(movie["movieId"])

        if movie_id in liked_ids:
            continue

        results.append(
            {
                "movie_id": movie_id,
                "title": movie["title"],
                "genres": movie.get("genres", ""),
                "similarity_score": float(distances[0][pos]),
            }
        )

    return results[:n_results]


# ============================================================================
# Caching utilities (optional, for performance)
# ============================================================================


def get_cached_recommendations(
    conn: sqlite3.Connection,
    profile_ids: List[str],
    cache_type: str = "collab",
) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve cached recommendations for a set of profiles.

    Args:
        conn: Database connection
        profile_ids: List of profile IDs
        cache_type: Type of cache ("collab" or "single")

    Returns:
        Cached recommendations or None if not found or expired
    """
    import json
    from datetime import datetime

    # Create cache key from sorted profile IDs and cache type
    sorted_ids = sorted(profile_ids)
    cache_key = f"{cache_type}_{','.join(sorted_ids)}"

    cursor = conn.cursor()
    cursor.execute(
        """SELECT recommendations FROM cached_recommendations
           WHERE cache_key = ? AND expires_at > ?""",
        (cache_key, datetime.now()),
    )

    result = cursor.fetchone()
    if result:
        return json.loads(result[0])

    return None


def cache_recommendations(
    conn: sqlite3.Connection,
    profile_ids: List[str],
    recommendations: List[Dict[str, Any]],
    ttl_minutes: int = 30,
    cache_type: str = "collab",
) -> None:
    """
    Cache recommendations for a set of profiles.

    Args:
        conn: Database connection
        profile_ids: List of profile IDs
        recommendations: Recommendation results to cache
        ttl_minutes: Time-to-live in minutes (default 30)
        cache_type: Type of cache ("collab" or "single")
    """
    import json
    from datetime import datetime, timedelta

    sorted_ids = sorted(profile_ids)
    cache_key = f"{cache_type}_{','.join(sorted_ids)}"

    expires_at = datetime.now() + timedelta(minutes=ttl_minutes)

    conn.execute(
        """INSERT OR REPLACE INTO cached_recommendations
           (cache_key, profile_ids, recommendations, created_at, expires_at)
           VALUES (?, ?, ?, ?, ?)""",
        (cache_key, ",".join(sorted_ids), json.dumps(recommendations), datetime.now(), expires_at),
    )
    conn.commit()
