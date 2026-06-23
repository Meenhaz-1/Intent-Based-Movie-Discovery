#!/bin/bash

# Run automated tests before committing to GitHub
# Usage: ./run_tests.sh

set -e

echo "======================================================================"
echo "Movie Recommender - Automated Test Suite (5 User Flows)"
echo "======================================================================"
echo ""

# Check if backend is running
echo "Checking if backend is running on http://localhost:8000..."
if ! curl -s http://localhost:8000/api/search/semantic -X POST -H "Content-Type: application/json" -d '{"query":"test"}' > /dev/null 2>&1; then
    echo "ERROR: Backend not running on http://localhost:8000"
    echo ""
    echo "Start backend with:"
    echo "  cd backend"
    echo "  python -m uvicorn src.main:app --reload"
    exit 1
fi

echo "✓ Backend is running"
echo ""

# Install test dependencies
echo "Installing test dependencies..."
pip install -q -r backend/requirements-test.txt

echo "✓ Dependencies installed"
echo ""

# Run tests
echo "Running automated test suite..."
echo "======================================================================"
cd backend
python -m pytest tests/test_five_user_flows.py -v --tb=short

exit_code=$?

echo ""
echo "======================================================================"
if [ $exit_code -eq 0 ]; then
    echo "SUCCESS: All tests passed!"
    echo "Safe to commit to GitHub"
else
    echo "FAILURE: Some tests failed"
    echo "Review errors above before committing"
fi
echo "======================================================================"

exit $exit_code
