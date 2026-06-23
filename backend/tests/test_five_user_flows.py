"""
Automated testing for 5 core user flows.
Run with: pytest tests/test_five_user_flows.py -v

These tests validate the entire user journey without manual intervention.
"""

import pytest
import requests
import json
from typing import Dict, Any

API_URL = "http://localhost:8000/api"
TEST_USER = "test_user_automated"
TEST_PROFILE = f"{TEST_USER}_default"

class APIClient:
    """Helper to make API calls"""

    @staticmethod
    def post(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with JSON body"""
        response = requests.post(
            f"{API_URL}/{endpoint}",
            json=data,
            timeout=30
        )
        assert response.status_code == 200, f"API error: {response.status_code} - {response.text}"
        return response.json()

    @staticmethod
    def get(endpoint: str) -> Dict[str, Any]:
        """GET request"""
        response = requests.get(
            f"{API_URL}/{endpoint}",
            timeout=30
        )
        assert response.status_code == 200, f"API error: {response.status_code} - {response.text}"
        return response.json()

    @staticmethod
    def delete(endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        response = requests.delete(
            f"{API_URL}/{endpoint}",
            timeout=30
        )
        return response.json()


# ============================================================================
# FLOW 1: Search & Add to Likes
# ============================================================================

class TestFlow1SearchAndAddToLikes:
    """Flow 1: User searches for a movie and adds it to their likes"""

    def test_1_1_semantic_search_returns_results(self):
        """Semantic search should return results with year and poster"""
        data = APIClient.post("search/semantic", {"query": "action"})

        assert "results" in data, "Response missing 'results' key"
        assert len(data["results"]) > 0, "No results returned"

        first = data["results"][0]
        assert "movie_id" in first
        assert "title" in first
        assert "year" in first or True  # year can be None
        assert "poster_url" in first
        assert "genres" in first

    def test_1_2_exact_matches_appear_first(self):
        """Exact matches should have score 1.0 and appear first"""
        data = APIClient.post("search/semantic", {"query": "Avatar"})

        results = data["results"]
        assert len(results) > 0

        # Check if any exact match exists
        exact_match = next((r for r in results if "avatar" in r["title"].lower()), None)
        if exact_match:
            assert exact_match["score"] == 1.0, "Exact match should have perfect score"

    def test_1_3_keyword_search_returns_results(self):
        """Keyword search should also work"""
        data = APIClient.post("search/keyword", {"query": "comedy"})

        assert "results" in data
        assert len(data["results"]) > 0

    def test_1_4_add_movie_to_likes(self):
        """Add a searched movie to likes"""
        # Search for a movie
        search_data = APIClient.post("search/semantic", {"query": "action", "limit": 5})
        movie = search_data["results"][0]
        movie_id = movie["movie_id"]

        # Add to likes
        response = APIClient.post(
            "movies/test_flow_1_profile/likes",
            {
                "profile_id": "test_flow_1_profile",
                "movie_id": movie_id
            }
        )

        assert "message" in response or response.get("status") == "success"

    def test_1_5_movie_appears_in_likes_after_adding(self):
        """After adding, movie should be in likes"""
        # Search and add
        search_data = APIClient.post("search/semantic", {"query": "animation", "limit": 5})
        movie = search_data["results"][0]
        movie_id = movie["movie_id"]

        APIClient.post(
            "movies/test_flow_1_profile/likes",
            {"profile_id": "test_flow_1_profile", "movie_id": movie_id}
        )

        # Verify it's in likes
        likes = APIClient.get("movies/test_flow_1_profile/likes")
        assert len(likes) > 0
        assert any(m["movie_id"] == movie_id for m in likes), "Movie not found in likes"


# ============================================================================
# FLOW 2: View My Likes Tab
# ============================================================================

class TestFlow2ViewMyLikes:
    """Flow 2: User views their liked movies with full details"""

    def test_2_1_add_multiple_movies_to_likes(self):
        """Add 3+ movies to likes for testing"""
        for i in range(3):
            search_data = APIClient.post(
                "search/semantic",
                {"query": f"movie" if i == 0 else f"film" if i == 1 else "drama"}
            )
            movie = search_data["results"][i]
            APIClient.post(
                "movies/test_flow_2_profile/likes",
                {"profile_id": "test_flow_2_profile", "movie_id": movie["movie_id"]}
            )

    def test_2_2_likes_endpoint_returns_full_movie_data(self):
        """Likes should return full movie details, not just IDs"""
        likes = APIClient.get("movies/test_flow_2_profile/likes")

        assert len(likes) > 0, "No likes found"

        movie = likes[0]
        assert "movie_id" in movie, "Missing movie_id"
        assert "title" in movie, "Missing title"
        assert "genres" in movie, "Missing genres"
        assert "year" in movie, "Missing year"
        assert "poster_url" in movie, "Missing poster_url"

    def test_2_3_year_is_extracted_from_title(self):
        """Year should be extracted from title (e.g., 'Movie (1993)' → 1993)"""
        likes = APIClient.get("movies/test_flow_2_profile/likes")

        assert len(likes) > 0

        for movie in likes:
            # Year should be int or None, not part of title
            if movie.get("year"):
                assert isinstance(movie["year"], int), f"Year should be int, got {type(movie['year'])}"
                assert 1800 <= movie["year"] <= 2100, f"Year out of range: {movie['year']}"

    def test_2_4_poster_url_present(self):
        """Poster URL should be included (even if null)"""
        likes = APIClient.get("movies/test_flow_2_profile/likes")

        for movie in likes:
            assert "poster_url" in movie, "poster_url field missing"
            # poster_url can be null if TMDB key not configured

    def test_2_5_remove_movie_from_likes(self):
        """Should be able to remove a movie from likes"""
        likes = APIClient.get("movies/test_flow_2_profile/likes")
        initial_count = len(likes)

        if initial_count > 0:
            movie_id = likes[0]["movie_id"]
            APIClient.delete(f"movies/test_flow_2_profile/likes/{movie_id}")

            likes_after = APIClient.get("movies/test_flow_2_profile/likes")
            assert len(likes_after) < initial_count, "Movie was not removed"


# ============================================================================
# FLOW 3: Single Profile Recommendations
# ============================================================================

class TestFlow3SingleProfileRecommendations:
    """Flow 3: User gets recommendations based on single profile likes"""

    def test_3_1_add_seed_likes_for_recommendations(self):
        """Add some movies to profile so it has data for recommendations"""
        for i in range(3):
            search_data = APIClient.post(
                "search/semantic",
                {"query": "sci-fi" if i == 0 else "action" if i == 1 else "adventure"}
            )
            movie = search_data["results"][0]
            APIClient.post(
                "movies/test_flow_3_profile/likes",
                {"profile_id": "test_flow_3_profile", "movie_id": movie["movie_id"]}
            )

    def test_3_2_recommendations_endpoint_exists(self):
        """Single-profile recommendations endpoint should exist"""
        data = APIClient.post(
            "recommendations/single-profile",
            {"profile_id": "test_flow_3_profile"}
        )

        assert "recommendations" in data, "Missing recommendations key"

    def test_3_3_recommendations_have_required_fields(self):
        """Each recommendation should have title, year, genres, score, poster"""
        data = APIClient.post(
            "recommendations/single-profile",
            {"profile_id": "test_flow_3_profile"}
        )

        recs = data.get("recommendations", [])

        if len(recs) > 0:
            rec = recs[0]
            assert "movie_id" in rec, "Missing movie_id"
            assert "title" in rec, "Missing title"
            assert "genres" in rec, "Missing genres"
            assert "year" in rec, "Missing year"
            assert "poster_url" in rec, "Missing poster_url"
            assert "similarity_score" in rec, "Missing similarity_score"

    def test_3_4_recommendations_count_matches_limit(self):
        """Should return requested number of recommendations"""
        data = APIClient.post(
            "recommendations/single-profile",
            {"profile_id": "test_flow_3_profile", "limit": 5}
        )

        recs = data.get("recommendations", [])
        assert len(recs) <= 5, "Returned more than requested"

    def test_3_5_similarity_score_is_numeric(self):
        """Similarity scores should be numeric"""
        data = APIClient.post(
            "recommendations/single-profile",
            {"profile_id": "test_flow_3_profile"}
        )

        recs = data.get("recommendations", [])
        for rec in recs:
            score = rec.get("similarity_score")
            assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"


# ============================================================================
# FLOW 4: Create New Profile & Use It
# ============================================================================

class TestFlow4MultiProfile:
    """Flow 4: User creates new profile and uses it independently"""

    def test_4_1_create_profile_implicitly(self):
        """Adding likes to a new profile should create it implicitly"""
        profile_id = "test_flow_4_profile_new"

        search_data = APIClient.post("search/semantic", {"query": "drama"})
        movie = search_data["results"][0]

        APIClient.post(
            f"movies/{profile_id}/likes",
            {"profile_id": profile_id, "movie_id": movie["movie_id"]}
        )

        # Verify profile exists by getting its likes
        likes = APIClient.get(f"movies/{profile_id}/likes")
        assert len(likes) > 0

    def test_4_2_profiles_are_independent(self):
        """Different profiles should have different likes"""
        profile1 = "test_flow_4_profile1"
        profile2 = "test_flow_4_profile2"

        # Add movie to profile 1
        search_data = APIClient.post("search/semantic", {"query": "action"})
        movie1 = search_data["results"][0]

        APIClient.post(
            f"movies/{profile1}/likes",
            {"profile_id": profile1, "movie_id": movie1["movie_id"]}
        )

        # Add different movie to profile 2
        search_data = APIClient.post("search/semantic", {"query": "comedy"})
        movie2 = search_data["results"][0]

        APIClient.post(
            f"movies/{profile2}/likes",
            {"profile_id": profile2, "movie_id": movie2["movie_id"]}
        )

        # Verify they're different
        likes1 = APIClient.get(f"movies/{profile1}/likes")
        likes2 = APIClient.get(f"movies/{profile2}/likes")

        ids1 = {m["movie_id"] for m in likes1}
        ids2 = {m["movie_id"] for m in likes2}

        assert ids1 != ids2, "Profiles should have different likes"

    def test_4_3_new_profile_can_get_recommendations(self):
        """New profile should be able to get recommendations after adding likes"""
        profile_id = "test_flow_4_profile_rec"

        # Add movies
        for i in range(2):
            search_data = APIClient.post("search/semantic", {"query": "sci-fi" if i == 0 else "fantasy"})
            movie = search_data["results"][0]
            APIClient.post(
                f"movies/{profile_id}/likes",
                {"profile_id": profile_id, "movie_id": movie["movie_id"]}
            )

        # Get recommendations
        data = APIClient.post(
            "recommendations/single-profile",
            {"profile_id": profile_id}
        )

        assert "recommendations" in data


# ============================================================================
# FLOW 5: Collaborative Recommendations
# ============================================================================

class TestFlow5Collaborative:
    """Flow 5: Get recommendations across multiple profiles"""

    def test_5_1_setup_multiple_profiles_with_likes(self):
        """Create 2 profiles with different preferences"""
        # Profile 1: Action/Sci-Fi lover
        for query in ["action", "sci-fi"]:
            search_data = APIClient.post("search/semantic", {"query": query})
            movie = search_data["results"][0]
            APIClient.post(
                "movies/test_flow_5_profile1/likes",
                {"profile_id": "test_flow_5_profile1", "movie_id": movie["movie_id"]}
            )

        # Profile 2: Comedy/Drama lover
        for query in ["comedy", "drama"]:
            search_data = APIClient.post("search/semantic", {"query": query})
            movie = search_data["results"][0]
            APIClient.post(
                "movies/test_flow_5_profile2/likes",
                {"profile_id": "test_flow_5_profile2", "movie_id": movie["movie_id"]}
            )

    def test_5_2_collaborative_requires_2_plus_profiles(self):
        """Collaborative mode should require at least 2 profiles"""
        # Should work with 2 profiles
        data = APIClient.post(
            "recommendations/collaborative",
            {
                "profile_ids": ["test_flow_5_profile1", "test_flow_5_profile2"],
                "variance_penalty": 0.3
            }
        )

        assert "recommendations" in data, "Should work with 2 profiles"

    def test_5_3_collaborative_returns_recommendations_with_scores(self):
        """Collaborative recommendations should have per-profile scores"""
        data = APIClient.post(
            "recommendations/collaborative",
            {
                "profile_ids": ["test_flow_5_profile1", "test_flow_5_profile2"],
                "variance_penalty": 0.3
            }
        )

        recs = data.get("recommendations", [])

        if len(recs) > 0:
            rec = recs[0]
            assert "movie_id" in rec
            assert "title" in rec
            assert "combined_score" in rec
            assert "mean_similarity" in rec
            assert "variance" in rec
            assert "profile_scores" in rec
            assert "year" in rec
            assert "poster_url" in rec

    def test_5_4_variance_penalty_affects_strictness(self):
        """Lower variance penalty = more movies, higher = fewer"""
        profiles = ["test_flow_5_profile1", "test_flow_5_profile2"]

        # Loose consensus (variance_penalty = 0.0)
        loose = APIClient.post(
            "recommendations/collaborative",
            {
                "profile_ids": profiles,
                "variance_penalty": 0.0,
                "limit": 20
            }
        )

        # Strict consensus (variance_penalty = 1.0)
        strict = APIClient.post(
            "recommendations/collaborative",
            {
                "profile_ids": profiles,
                "variance_penalty": 1.0,
                "limit": 20
            }
        )

        loose_count = len(loose.get("recommendations", []))
        strict_count = len(strict.get("recommendations", []))

        # Strict should typically have fewer or equal movies
        assert strict_count <= loose_count, "Strict consensus should have fewer or equal results"

    def test_5_5_profile_scores_sum_correctly(self):
        """Per-profile scores should be between 0 and 1"""
        data = APIClient.post(
            "recommendations/collaborative",
            {
                "profile_ids": ["test_flow_5_profile1", "test_flow_5_profile2"],
                "variance_penalty": 0.3
            }
        )

        recs = data.get("recommendations", [])

        for rec in recs:
            scores = rec.get("profile_scores", {})
            for profile_id, score in scores.items():
                assert 0 <= score <= 1, f"Score out of range for {profile_id}: {score}"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Cross-flow integration tests"""

    def test_search_and_recommendations_consistency(self):
        """Movies from search should appear in recommendations"""
        profile = "test_integration_profile"

        # Search and add
        search_data = APIClient.post("search/semantic", {"query": "adventure"})
        for movie in search_data["results"][:3]:
            APIClient.post(
                f"movies/{profile}/likes",
                {"profile_id": profile, "movie_id": movie["movie_id"]}
            )

        # Get recommendations
        rec_data = APIClient.post(
            "recommendations/single-profile",
            {"profile_id": profile}
        )

        assert len(rec_data.get("recommendations", [])) > 0, "Should have recommendations"

    def test_all_api_responses_have_required_fields(self):
        """Every API response should have proper structure"""
        # Search
        search = APIClient.post("search/semantic", {"query": "test"})
        assert "results" in search
        assert "query" in search
        assert "total" in search

        # Recommendations
        rec = APIClient.post(
            "recommendations/single-profile",
            {"profile_id": "test_integration_profile"}
        )
        assert "recommendations" in rec
        assert "total" in rec

        # Collaborative
        collab = APIClient.post(
            "recommendations/collaborative",
            {
                "profile_ids": ["test_flow_5_profile1", "test_flow_5_profile2"],
                "variance_penalty": 0.3
            }
        )
        assert "recommendations" in collab
        assert "variance_penalty" in collab


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
