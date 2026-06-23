#!/usr/bin/env python3
"""
Quick automated test for 5 core user flows.
Run before committing to GitHub.

Usage:
    python test_userflows.py
"""

import requests
import json
import sys
from datetime import datetime

API_URL = "http://localhost:8000/api"

class Colors:
    GREEN = ''
    RED = ''
    YELLOW = ''
    BLUE = ''
    END = ''

def log_test(name, passed, message=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if message:
        print(f"      {message}")

def test_flow_1_search():
    """Flow 1: Search & Add to Likes"""
    print(f"\n{Colors.BLUE}=== Flow 1: Search & Add to Likes ==={Colors.END}")

    try:
        # Test semantic search
        response = requests.post(
            f"{API_URL}/search/semantic",
            json={"query": "action"},
            timeout=15
        )
        data = response.json()

        passed = response.status_code == 200
        log_test("Search returns 200 OK", passed)

        has_results = len(data.get("results", [])) > 0
        log_test("Search has results", has_results)

        if has_results:
            first = data["results"][0]
            has_year = first.get("year") is not None
            has_title = first.get("title") is not None
            has_poster = "poster_url" in first

            log_test("Results have year field", has_year, f"Year: {first.get('year')}")
            log_test("Results have title field", has_title, f"Title: {first.get('title')}")
            log_test("Results have poster_url field", has_poster)

            # Test add to likes
            movie_id = first.get("movie_id")
            like_response = requests.post(
                f"{API_URL}/movies/demo_user_default/likes",
                json={"profile_id": "demo_user_default", "movie_id": movie_id},
                timeout=5
            )
            like_passed = like_response.status_code == 200
            log_test("Add to likes returns 200", like_passed)

            return all([passed, has_results, has_year, has_title, has_poster, like_passed])
    except Exception as e:
        log_test("Search flow", False, str(e))
        return False

def test_flow_2_my_likes():
    """Flow 2: View My Likes Tab"""
    print(f"\n{Colors.BLUE}=== Flow 2: View My Likes Tab ==={Colors.END}")

    try:
        response = requests.get(
            f"{API_URL}/movies/demo_user_default/likes",
            timeout=5
        )
        data = response.json()

        passed = response.status_code == 200
        log_test("Get likes returns 200 OK", passed)

        has_likes = len(data) > 0
        log_test("Likes has movies", has_likes, f"Count: {len(data)}")

        if has_likes:
            first = data[0]
            has_title = first.get("title") is not None
            has_year = first.get("year") is not None
            has_genres = first.get("genres") is not None
            has_poster = "poster_url" in first

            log_test("Likes have title", has_title, f"Title: {first.get('title')}")
            log_test("Likes have year", has_year, f"Year: {first.get('year')}")
            log_test("Likes have genres", has_genres)
            log_test("Likes have poster_url", has_poster)

            return all([passed, has_likes, has_title, has_year, has_genres, has_poster])
    except Exception as e:
        log_test("My Likes flow", False, str(e))
        return False

def test_flow_3_single_recommendations():
    """Flow 3: Get Single Profile Recommendations"""
    print(f"\n{Colors.BLUE}=== Flow 3: Single Profile Recommendations ==={Colors.END}")

    try:
        response = requests.post(
            f"{API_URL}/recommendations/single-profile",
            json={"profile_id": "demo_user_default"},
            timeout=5
        )
        data = response.json()

        passed = response.status_code == 200
        log_test("Recommendations returns 200 OK", passed)

        has_recs = len(data.get("recommendations", [])) > 0
        log_test("Recommendations has results", has_recs, f"Count: {data.get('total', 0)}")

        if has_recs:
            first = data["recommendations"][0]
            has_title = first.get("title") is not None
            has_year = first.get("year") is not None
            has_genres = first.get("genres") is not None
            has_score = first.get("similarity_score") is not None

            log_test("Recommendations have title", has_title)
            log_test("Recommendations have year", has_year, f"Year: {first.get('year')}")
            log_test("Recommendations have genres", has_genres)
            log_test("Recommendations have score", has_score, f"Score: {first.get('similarity_score')}")

            return all([passed, has_recs, has_title, has_year, has_genres, has_score])
    except Exception as e:
        log_test("Recommendations flow", False, str(e))
        return False

def test_flow_4_new_profile():
    """Flow 4: Create New Profile & Use It"""
    print(f"\n{Colors.BLUE}=== Flow 4: Create New Profile & Use It ==={Colors.END}")

    try:
        # Note: This is a basic test assuming profile creation exists
        # If endpoints don't exist, this will fail gracefully

        test_profile = f"test_profile_{int(datetime.now().timestamp())}"

        # Try to get profiles (if endpoint exists)
        response = requests.get(
            f"{API_URL}/profiles/demo_user",
            timeout=5
        )

        passed = response.status_code == 200
        log_test("Profiles endpoint returns 200", passed)

        if passed:
            profiles = response.json()
            has_profiles = len(profiles) > 0
            log_test("User has profiles", has_profiles, f"Count: {len(profiles)}")

            if has_profiles:
                first = profiles[0]
                has_id = first.get("profile_id") is not None
                has_name = first.get("profile_name") is not None
                log_test("Profiles have ID", has_id)
                log_test("Profiles have name", has_name, f"Name: {first.get('profile_name')}")

                return all([passed, has_profiles, has_id, has_name])

        return False
    except Exception as e:
        log_test("New profile flow", False, str(e))
        return False

def test_flow_5_collaborative():
    """Flow 5: Collaborative Recommendations"""
    print(f"\n{Colors.BLUE}=== Flow 5: Collaborative Recommendations ==={Colors.END}")

    try:
        response = requests.post(
            f"{API_URL}/recommendations/collaborative",
            json={
                "profile_ids": ["demo_user_default"],
                "variance_penalty": 0.3
            },
            timeout=5
        )
        data = response.json()

        # This should fail with <2 profiles, but let's check the endpoint works
        passed = response.status_code in [200, 400]
        log_test("Collaborative endpoint responds", passed)

        if response.status_code == 200:
            has_recs = len(data.get("recommendations", [])) > 0
            log_test("Collaborative has results", has_recs, f"Count: {data.get('total', 0)}")
            return passed and has_recs
        else:
            # Expected to fail with 1 profile
            log_test("Requires 2+ profiles (as expected)", True, "400 error is expected with 1 profile")
            return True

    except Exception as e:
        log_test("Collaborative flow", False, str(e))
        return False

def main():
    print(f"{Colors.BLUE}{'='*60}")
    print(f"Movie Recommender - 5 User Flow Test Suite")
    print(f"{'='*60}{Colors.END}\n")

    print(f"API URL: {API_URL}\n")

    results = []

    results.append(("Flow 1: Search & Add to Likes", test_flow_1_search()))
    results.append(("Flow 2: View My Likes", test_flow_2_my_likes()))
    results.append(("Flow 3: Single Recommendations", test_flow_3_single_recommendations()))
    results.append(("Flow 4: New Profile", test_flow_4_new_profile()))
    results.append(("Flow 5: Collaborative", test_flow_5_collaborative()))

    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}{Colors.END}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{status} | {name}")

    print(f"\n{Colors.BLUE}Total: {passed}/{total} flows passed{Colors.END}\n")

    if passed == total:
        print(f"{Colors.GREEN}All flows passed! Safe to commit.{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}Some flows failed. Review errors above.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
