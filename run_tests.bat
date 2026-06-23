@echo off
REM Automated test suite for Movie Recommender (5 User Flows)
REM Run before committing to GitHub

setlocal enabledelayedexpansion

cls
echo ======================================================================
echo Movie Recommender - Automated Test Suite (5 User Flows)
echo ======================================================================
echo.

REM Check if backend is running
echo Checking if backend is running on http://localhost:8000...
curl -s http://localhost:8000/api/search/semantic -X POST -H "Content-Type: application/json" -d "{\"query\":\"test\"}" >nul 2>&1

if errorlevel 1 (
    echo ERROR: Backend not running on http://localhost:8000
    echo.
    echo Start backend with:
    echo   cd backend
    echo   python -m uvicorn src.main:app --reload
    exit /b 1
)

echo ^ Backend is running
echo.

REM Install test dependencies
echo Installing test dependencies...
pip install -q -r backend\requirements-test.txt

echo ^ Dependencies installed
echo.

REM Run tests
echo Running automated test suite...
echo ======================================================================
cd backend
python -m pytest tests\test_five_user_flows.py -v --tb=short

set test_result=%errorlevel%

cd ..
echo.
echo ======================================================================
if %test_result% equ 0 (
    echo SUCCESS: All tests passed!
    echo Safe to commit to GitHub
) else (
    echo FAILURE: Some tests failed
    echo Review errors above before committing
)
echo ======================================================================

exit /b %test_result%
