# Automated Test Suite

Comprehensive automated testing for all 5 core user flows. **No manual testing required.**

## Quick Start

### 1. Start Backend
```bash
cd backend
python -m uvicorn src.main:app --reload
```

Backend should be running on `http://localhost:8000`

### 2. Run Tests (Windows)
```bash
run_tests.bat
```

### 3. Run Tests (Mac/Linux)
```bash
chmod +x run_tests.sh
./run_tests.sh
```

## Test Coverage

The automated test suite covers all 5 critical user flows:

### Flow 1: Search & Add to Likes
```
✓ Semantic search returns results with year and poster
✓ Exact matches appear first with perfect score (1.0)
✓ Keyword search works
✓ Can add movie to likes
✓ Movie appears in likes after adding
```

### Flow 2: View My Likes Tab
```
✓ Can add multiple movies to likes
✓ Likes endpoint returns full movie data (not just IDs)
✓ Year is properly extracted from title
✓ Poster URL is included in response
✓ Can remove movie from likes
```

### Flow 3: Single Profile Recommendations
```
✓ Recommendations endpoint exists and returns data
✓ Each recommendation has: title, year, genres, poster, score
✓ Returns requested limit of recommendations
✓ Similarity scores are numeric
```

### Flow 4: Create New Profile & Use It
```
✓ Profiles are created implicitly when first used
✓ Different profiles have independent likes
✓ New profiles can get recommendations
```

### Flow 5: Collaborative Recommendations
```
✓ Requires 2+ profiles
✓ Returns recommendations with per-profile scores
✓ Variance penalty affects strictness (0.0 = loose, 1.0 = strict)
✓ Profile scores are between 0.0 and 1.0
```

### Integration Tests
```
✓ Search and recommendations are consistent
✓ All API responses have required fields
```

## What Gets Tested

### API Endpoints
- `POST /api/search/semantic` - Semantic search
- `POST /api/search/keyword` - Keyword search
- `GET /api/movies/{profile_id}/likes` - Get liked movies
- `POST /api/movies/{profile_id}/likes` - Add to likes
- `DELETE /api/movies/{profile_id}/likes/{movie_id}` - Remove from likes
- `POST /api/recommendations/single-profile` - Single profile recs
- `POST /api/recommendations/collaborative` - Collaborative recs

### Response Structure
- All search results have: movie_id, title, genres, year, poster_url, score
- All likes have: movie_id, title, genres, year, poster_url
- All recommendations have proper fields including year and poster_url
- Years are extracted from titles and returned as integers
- Poster URLs are included (can be null if TMDB key not configured)

### Data Integrity
- Movies added to one profile don't appear in another
- Removed movies are actually deleted
- Variance penalty parameter affects recommendation count
- Per-profile scores in collaborative mode are in valid range [0, 1]

## Test Results

When you run the tests, you'll see output like:

```
======================================================================
Movie Recommender - Automated Test Suite (5 User Flows)
======================================================================

✓ Backend is running
✓ Dependencies installed

Running automated test suite...
======================================================================

test_five_user_flows.py::TestFlow1SearchAndAddToLikes::test_1_1_semantic_search_returns_results PASSED
test_five_user_flows.py::TestFlow1SearchAndAddToLikes::test_1_2_exact_matches_appear_first PASSED
test_five_user_flows.py::TestFlow1SearchAndAddToLikes::test_1_3_keyword_search_returns_results PASSED
test_five_user_flows.py::TestFlow1SearchAndAddToLikes::test_1_4_add_movie_to_likes PASSED
test_five_user_flows.py::TestFlow1SearchAndAddToLikes::test_1_5_movie_appears_in_likes_after_adding PASSED
...

test_five_user_flows.py::TestIntegration::test_all_api_responses_have_required_fields PASSED

======================================================================
SUCCESS: All tests passed!
Safe to commit to GitHub
======================================================================
```

## GitHub Actions CI/CD

Tests run automatically on every push to `main` branch and on all pull requests.

Check results at: https://github.com/Meenhaz-1/Intent-Based-Movie-Discovery/actions

## Troubleshooting

### Backend not responding
```
ERROR: Backend not running on http://localhost:8000
```
**Solution:** Start backend first
```bash
cd backend
python -m uvicorn src.main:app --reload
```

### Test timeout errors
```
pytest.exceptions.Timeout
```
**Solution:** Backend is slow. Try:
1. Stop and restart backend
2. Wait 10 seconds after starting
3. Increase timeout in test file (currently 30 seconds)

### TMDB poster URLs are null
This is expected. Poster URLs require `TMDB_API_KEY` environment variable:
```bash
export TMDB_API_KEY=your_key_here
```
Tests pass with or without posters configured.

### Specific test fails but others pass
Run individual test:
```bash
cd backend
python -m pytest tests/test_five_user_flows.py::TestFlow1SearchAndAddToLikes -v
```

## Before Committing

**Always run tests before committing:**

```bash
# Run tests
./run_tests.bat  # Windows
# or
./run_tests.sh   # Mac/Linux

# If all pass:
git add .
git commit -m "Feature: description

- All 5 user flows tested and passing"
git push
```

## Test Isolation

Each test flow uses different test profiles to avoid interference:
- Flow 1: `test_flow_1_profile`
- Flow 2: `test_flow_2_profile`
- Flow 3: `test_flow_3_profile`
- Flow 4: `test_flow_4_profile*`
- Flow 5: `test_flow_5_profile1`, `test_flow_5_profile2`

Tests are idempotent and can be run multiple times.

## Continuous Integration

The `.github/workflows/test.yml` file runs tests on every push automatically.

View test results: **Actions** tab → **Automated Tests**

---

**Key Rule: If tests don't pass, don't commit. If tests pass, you're good to go.**
