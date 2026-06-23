# Pull Request: Automated Testing Suite & Environment Configuration

This PR adds:
- 25 automated pytest test cases covering all 5 user flows
- Complete test infrastructure with CI/CD automation
- Production-ready environment configuration
- Bug fixes for TMDB error handling

## Branch Info
- Feature Branch: feature/automated-testing-and-env-config
- Target: main
- Status: Ready for merge

## Summary of Changes
1. Automated Testing: backend/tests/test_five_user_flows.py (25 tests)
2. Test Runners: run_tests.bat (Windows), run_tests.sh (Mac/Linux)
3. CI/CD: .github/workflows/test.yml (GitHub Actions)
4. Environment: backend/.env, frontend/.env, ENV_SETUP.md
5. Bug Fixes: backend/routes/movies.py, backend/tmdb_helper.py

## How to Test
1. Start backend: python -m uvicorn src.main:app --reload
2. Run tests: run_tests.bat (Windows) or ./run_tests.sh (Mac/Linux)
3. All 25 tests should pass

## Optional Setup
- Add TMDB_API_KEY to backend/.env for movie posters
- See ENV_SETUP.md for complete configuration guide
