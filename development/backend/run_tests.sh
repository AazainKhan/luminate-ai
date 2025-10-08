#!/bin/bash

# Test runner for Luminate AI intelligent logic layer

echo "======================================"
echo "Luminate AI - Intelligent Logic Tests"
echo "======================================"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "⚠️  pytest not found. Installing test dependencies..."
    pip install -r tests/requirements.txt
fi

echo "🧪 Running intelligent logic layer tests..."
echo ""

# Run all tests with verbose output
python -m pytest tests/ -v --tb=short \
    --cov=langgraph/agents \
    --cov-report=term-missing \
    --cov-report=html:tests/coverage_html

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "======================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "Coverage report generated in: tests/coverage_html/index.html"
else
    echo "❌ Some tests failed. See output above for details."
fi

echo "======================================"

exit $TEST_EXIT_CODE
