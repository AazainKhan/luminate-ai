# Testing Guide for Luminate AI Improvements

This guide explains how to run the tests for the backend and frontend improvements.

## Prerequisites

### Backend Tests

Install test dependencies:
```bash
pip install pytest pytest-asyncio httpx
```

Or install from requirements if available:
```bash
pip install -r requirements.txt
```

### Frontend Tests

Already configured in the Chrome extension:
```bash
cd chrome-extension
npm install  # If not already installed
```

## Running Backend Tests

### Unit Tests (Middleware)

Test the middleware components (cache, rate limiter, validator, metrics):

```bash
cd /home/runner/work/luminate-ai/luminate-ai
python -m pytest tests/test_middleware.py -v
```

Expected output:
```
tests/test_middleware.py::TestInMemoryCache::test_cache_set_and_get PASSED
tests/test_middleware.py::TestInMemoryCache::test_cache_expiration PASSED
tests/test_middleware.py::TestInMemoryCache::test_cache_miss PASSED
tests/test_middleware.py::TestInMemoryCache::test_cache_clear PASSED
tests/test_middleware.py::TestRateLimiter::test_within_limit PASSED
tests/test_middleware.py::TestRateLimiter::test_exceeds_limit PASSED
tests/test_middleware.py::TestRateLimiter::test_window_reset PASSED
tests/test_middleware.py::TestRateLimiter::test_multiple_clients PASSED
tests/test_middleware.py::TestRateLimiter::test_get_remaining PASSED
tests/test_middleware.py::TestRequestValidator::test_sanitize_query_whitespace PASSED
tests/test_middleware.py::TestRequestValidator::test_sanitize_query_length_limit PASSED
tests/test_middleware.py::TestRequestValidator::test_validate_n_results_clamps_low PASSED
tests/test_middleware.py::TestRequestValidator::test_validate_n_results_clamps_high PASSED
tests/test_middleware.py::TestRequestValidator::test_validate_n_results_valid PASSED
tests/test_middleware.py::TestRequestValidator::test_validate_score_range PASSED
tests/test_middleware.py::TestMetricsCollector::test_record_request PASSED
tests/test_middleware.py::TestMetricsCollector::test_record_error PASSED
tests/test_middleware.py::TestMetricsCollector::test_success_rate PASSED
tests/test_middleware.py::TestMetricsCollector::test_endpoint_tracking PASSED
tests/test_middleware.py::TestMetricsCollector::test_average_response_time PASSED
```

### Integration Tests (API Endpoints)

**Note**: These tests require ChromaDB to be set up. Some tests may skip if ChromaDB is not available.

```bash
cd /home/runner/work/luminate-ai/luminate-ai
python -m pytest tests/test_api_integration.py -v
```

Expected behavior:
- ✅ Tests pass if ChromaDB is available
- ⚠️ Some tests may skip if ChromaDB is not initialized (expected)
- ❌ Tests fail if there are actual bugs in the code

### Run All Tests

```bash
cd /home/runner/work/luminate-ai/luminate-ai
python -m pytest tests/ -v
```

## Running Frontend Tests

### Unit Tests

```bash
cd chrome-extension
npm test
```

### Run Tests in UI Mode

```bash
cd chrome-extension
npm run test:ui
```

### Coverage Report

```bash
cd chrome-extension
npm run test:coverage
```

## Manual Testing

### Backend Manual Testing

1. Start the backend server:
```bash
cd development/backend
python fastapi_service/main.py
```

2. Test endpoints with curl:

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Stats (with new metrics):**
```bash
curl http://localhost:8000/stats
```

**Navigate Query (with caching):**
```bash
curl -X POST http://localhost:8000/langgraph/navigate \
  -H "Content-Type: application/json" \
  -d '{"query": "What is backpropagation?"}'
```

**Test Caching** (should be instant on second call):
```bash
# First call (slow)
time curl -X POST http://localhost:8000/langgraph/navigate \
  -H "Content-Type: application/json" \
  -d '{"query": "What is backpropagation?"}'

# Second call (fast - cached)
time curl -X POST http://localhost:8000/langgraph/navigate \
  -H "Content-Type: application/json" \
  -d '{"query": "What is backpropagation?"}'
```

**Test Rate Limiting:**
```bash
# Send 70 requests rapidly (should get 429 after 60)
for i in {1..70}; do
  curl -s -X POST http://localhost:8000/langgraph/navigate \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' | grep -o "429\|200" &
done
wait
```

**Save Conversation:**
```bash
curl -X POST http://localhost:8000/conversation/save \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_123",
    "messages": [
      {
        "role": "user",
        "content": "What is machine learning?",
        "timestamp": "2024-01-01T12:00:00Z"
      }
    ]
  }'
```

**Load Conversation:**
```bash
curl http://localhost:8000/conversation/load/test_session_123
```

**Delete Conversation:**
```bash
curl -X DELETE http://localhost:8000/conversation/test_session_123
```

### Frontend Manual Testing

1. Build the extension:
```bash
cd chrome-extension
npm run build
```

2. Load in Chrome:
   - Go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `chrome-extension/dist`

3. Test features:
   - ✅ Open side panel on Blackboard page
   - ✅ Ask a question
   - ✅ Verify skeleton loader appears
   - ✅ Click copy button on response
   - ✅ Reload extension and verify history persists
   - ✅ Click clear history button
   - ✅ Try asking during backend downtime (should see error with retry button)
   - ✅ Click retry button

## Troubleshooting

### Backend Tests Fail with "ModuleNotFoundError"

Make sure you're in the right directory and Python can find the modules:
```bash
cd /home/runner/work/luminate-ai/luminate-ai
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m pytest tests/ -v
```

### ChromaDB Not Available

If you see "ChromaDB not initialized" errors:
1. Make sure ChromaDB is set up:
   ```bash
   cd development/backend
   python setup_chromadb.py
   ```

2. Or skip integration tests:
   ```bash
   pytest tests/test_middleware.py -v  # Only run middleware tests
   ```

### Frontend Build Errors

If TypeScript errors occur:
```bash
cd chrome-extension
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Rate Limiting During Tests

If you hit rate limits during testing:
1. Wait 60 seconds for window to reset
2. Or temporarily increase limit in `middleware.py`:
   ```python
   rate_limiter = RateLimiter(max_requests=1000, window_seconds=60)
   ```

## Continuous Integration

To run tests in CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio httpx
      - run: pytest tests/test_middleware.py -v
      
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: cd chrome-extension && npm install
      - run: cd chrome-extension && npm test
```

## Test Coverage Goals

- **Middleware**: 100% (all functions tested)
- **API Endpoints**: 80%+ (basic functionality tested)
- **Frontend Components**: 70%+ (critical paths tested)

## Writing New Tests

### Backend Test Template

```python
def test_new_feature():
    """Test description"""
    # Arrange
    setup_data = ...
    
    # Act
    result = function_under_test(setup_data)
    
    # Assert
    assert result == expected_value
```

### Frontend Test Template

```typescript
import { describe, it, expect } from 'vitest';

describe('Component Name', () => {
  it('should do something', () => {
    // Arrange
    const props = { ... };
    
    // Act
    const result = renderComponent(props);
    
    // Assert
    expect(result).toBe(expected);
  });
});
```

## Next Steps

1. Run all tests to verify everything works
2. Fix any failing tests
3. Add tests for any new features
4. Update this document with new test cases
5. Set up CI/CD for automatic testing
