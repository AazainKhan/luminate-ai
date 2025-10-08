"""
Unit tests for backend middleware
Tests caching, rate limiting, validation, and metrics
"""

import pytest
import time
from development.backend.fastapi_service.middleware import (
    InMemoryCache,
    RateLimiter,
    RequestValidator,
    MetricsCollector,
)


class TestInMemoryCache:
    """Test InMemoryCache functionality"""
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations"""
        cache = InMemoryCache(ttl_seconds=10)
        
        request_data = {"query": "test query"}
        response_data = {"result": "test result"}
        
        # Set cache
        cache.set(request_data, response_data)
        
        # Get cache
        cached = cache.get(request_data)
        assert cached == response_data
    
    def test_cache_expiration(self):
        """Test cache expiration after TTL"""
        cache = InMemoryCache(ttl_seconds=1)
        
        request_data = {"query": "test query"}
        response_data = {"result": "test result"}
        
        cache.set(request_data, response_data)
        
        # Should be cached
        assert cache.get(request_data) == response_data
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get(request_data) is None
    
    def test_cache_miss(self):
        """Test cache miss for unknown key"""
        cache = InMemoryCache(ttl_seconds=10)
        
        result = cache.get({"query": "unknown"})
        assert result is None
    
    def test_cache_clear(self):
        """Test clearing cache"""
        cache = InMemoryCache(ttl_seconds=10)
        
        cache.set({"query": "test1"}, {"result": "1"})
        cache.set({"query": "test2"}, {"result": "2"})
        
        assert cache.size() == 2
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get({"query": "test1"}) is None


class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    def test_within_limit(self):
        """Test requests within rate limit"""
        limiter = RateLimiter(max_requests=5, window_seconds=10)
        
        client_id = "test_client"
        
        # First 5 requests should be allowed
        for _ in range(5):
            assert limiter.is_allowed(client_id) is True
    
    def test_exceeds_limit(self):
        """Test requests exceeding rate limit"""
        limiter = RateLimiter(max_requests=3, window_seconds=10)
        
        client_id = "test_client"
        
        # First 3 requests allowed
        for _ in range(3):
            assert limiter.is_allowed(client_id) is True
        
        # 4th request should be denied
        assert limiter.is_allowed(client_id) is False
    
    def test_window_reset(self):
        """Test rate limit window reset"""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        client_id = "test_client"
        
        # Use up limit
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is False
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.is_allowed(client_id) is True
    
    def test_multiple_clients(self):
        """Test rate limiting for multiple clients"""
        limiter = RateLimiter(max_requests=2, window_seconds=10)
        
        # Client 1 uses their limit
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False
        
        # Client 2 should still have their limit
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client2") is True
    
    def test_get_remaining(self):
        """Test getting remaining requests"""
        limiter = RateLimiter(max_requests=5, window_seconds=10)
        
        client_id = "test_client"
        
        assert limiter.get_remaining(client_id) == 5
        
        limiter.is_allowed(client_id)
        assert limiter.get_remaining(client_id) == 4
        
        limiter.is_allowed(client_id)
        assert limiter.get_remaining(client_id) == 3


class TestRequestValidator:
    """Test RequestValidator functionality"""
    
    def test_sanitize_query_whitespace(self):
        """Test query sanitization removes extra whitespace"""
        query = "  test   query   with   spaces  "
        sanitized = RequestValidator.sanitize_query(query)
        assert sanitized == "test query with spaces"
    
    def test_sanitize_query_length_limit(self):
        """Test query length is limited"""
        long_query = "a" * 600
        sanitized = RequestValidator.sanitize_query(long_query)
        assert len(sanitized) == 500
    
    def test_validate_n_results_clamps_low(self):
        """Test n_results is clamped at minimum"""
        assert RequestValidator.validate_n_results(0) == 1
        assert RequestValidator.validate_n_results(-5) == 1
    
    def test_validate_n_results_clamps_high(self):
        """Test n_results is clamped at maximum"""
        assert RequestValidator.validate_n_results(100) == 50
        assert RequestValidator.validate_n_results(200) == 50
    
    def test_validate_n_results_valid(self):
        """Test valid n_results values"""
        assert RequestValidator.validate_n_results(10) == 10
        assert RequestValidator.validate_n_results(25) == 25
    
    def test_validate_score_range(self):
        """Test score validation range"""
        assert RequestValidator.validate_score(-0.5) == 0.0
        assert RequestValidator.validate_score(1.5) == 1.0
        assert RequestValidator.validate_score(0.5) == 0.5


class TestMetricsCollector:
    """Test MetricsCollector functionality"""
    
    def test_record_request(self):
        """Test recording requests"""
        metrics = MetricsCollector()
        
        metrics.record_request("/test", 100.0, success=True)
        
        stats = metrics.get_stats()
        assert stats["total_requests"] == 1
        assert stats["total_errors"] == 0
        assert stats["avg_response_time_ms"] == 100.0
    
    def test_record_error(self):
        """Test recording errors"""
        metrics = MetricsCollector()
        
        metrics.record_request("/test", 100.0, success=False)
        metrics.record_error("ValueError")
        
        stats = metrics.get_stats()
        assert stats["total_requests"] == 1
        assert stats["total_errors"] == 1
        assert stats["error_types"]["ValueError"] == 1
    
    def test_success_rate(self):
        """Test success rate calculation"""
        metrics = MetricsCollector()
        
        # 3 successes, 1 failure
        metrics.record_request("/test", 100.0, success=True)
        metrics.record_request("/test", 100.0, success=True)
        metrics.record_request("/test", 100.0, success=True)
        metrics.record_request("/test", 100.0, success=False)
        
        stats = metrics.get_stats()
        assert stats["total_requests"] == 4
        assert stats["success_rate"] == 0.75
    
    def test_endpoint_tracking(self):
        """Test endpoint call tracking"""
        metrics = MetricsCollector()
        
        metrics.record_request("/navigate", 100.0)
        metrics.record_request("/navigate", 100.0)
        metrics.record_request("/health", 50.0)
        
        stats = metrics.get_stats()
        assert stats["endpoint_calls"]["/navigate"] == 2
        assert stats["endpoint_calls"]["/health"] == 1
    
    def test_average_response_time(self):
        """Test average response time calculation"""
        metrics = MetricsCollector()
        
        metrics.record_request("/test", 100.0)
        metrics.record_request("/test", 200.0)
        metrics.record_request("/test", 300.0)
        
        stats = metrics.get_stats()
        assert stats["avg_response_time_ms"] == 200.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
