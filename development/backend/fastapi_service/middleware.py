"""
Enhanced middleware for FastAPI service
Provides caching, rate limiting, and request validation
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Callable
import time
import hashlib
import json
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# Simple in-memory cache
class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def _get_key(self, request_data: dict) -> str:
        """Generate cache key from request data"""
        data_str = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get(self, request_data: dict):
        """Get cached response if available and not expired"""
        key = self._get_key(request_data)
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                logger.info(f"Cache hit for key: {key[:8]}...")
                return cached_data
            else:
                # Expired, remove it
                del self.cache[key]
        return None
    
    def set(self, request_data: dict, response_data: dict):
        """Cache response data"""
        key = self._get_key(request_data)
        self.cache[key] = (response_data, time.time())
        logger.info(f"Cached response for key: {key[:8]}...")
    
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


# Rate limiter
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for this client"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean up old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for this client"""
        now = time.time()
        window_start = now - self.window_seconds
        
        recent_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(recent_requests))


# Request validator
class RequestValidator:
    """Validate and sanitize incoming requests"""
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize user query"""
        # Remove excessive whitespace
        query = " ".join(query.split())
        
        # Limit length
        max_length = 500
        if len(query) > max_length:
            query = query[:max_length]
        
        return query.strip()
    
    @staticmethod
    def validate_n_results(n: int) -> int:
        """Validate and clamp n_results parameter"""
        return max(1, min(50, n))
    
    @staticmethod
    def validate_score(score: float) -> float:
        """Validate and clamp score threshold"""
        return max(0.0, min(1.0, score))


# Metrics collector
class MetricsCollector:
    """Collect and track API metrics"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_errors = 0
        self.response_times = []
        self.endpoint_calls = defaultdict(int)
        self.error_types = defaultdict(int)
        self.start_time = datetime.now()
    
    def record_request(self, endpoint: str, response_time_ms: float, success: bool = True):
        """Record a request"""
        self.total_requests += 1
        self.endpoint_calls[endpoint] += 1
        self.response_times.append(response_time_ms)
        
        if not success:
            self.total_errors += 1
        
        # Keep only last 1000 response times to prevent memory bloat
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def record_error(self, error_type: str):
        """Record an error"""
        self.error_types[error_type] += 1
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "success_rate": (
                (self.total_requests - self.total_errors) / self.total_requests
                if self.total_requests > 0 else 0
            ),
            "avg_response_time_ms": round(avg_response_time, 2),
            "uptime_seconds": round(uptime, 2),
            "endpoint_calls": dict(self.endpoint_calls),
            "error_types": dict(self.error_types),
            "requests_per_second": (
                self.total_requests / uptime if uptime > 0 else 0
            )
        }


# Create global instances
cache = InMemoryCache(ttl_seconds=300)  # 5 minute TTL
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 60 requests per minute
metrics = MetricsCollector()
validator = RequestValidator()
