"""
Redis connection pool singleton for Luminate AI.

Usage:
    from app.redis_client import get_redis_client
    
    client = get_redis_client()
    client.set("key", "value", ex=3600)
    value = client.get("key")

Features:
- Connection pooling with max 20 connections
- Health check interval of 30 seconds
- Auto-reconnect on connection loss
- Thread-safe singleton pattern
"""

import redis
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Singleton pool instance
_redis_pool: Optional[redis.ConnectionPool] = None


def get_redis_pool() -> redis.ConnectionPool:
    """
    Get or create the Redis connection pool singleton.
    
    Returns:
        redis.ConnectionPool: The shared connection pool instance.
    """
    global _redis_pool
    
    if _redis_pool is None:
        logger.info(f"Creating Redis connection pool: {settings.redis_host}:{settings.redis_port}")
        
        _redis_pool = redis.ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            max_connections=20,
            health_check_interval=30,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            decode_responses=True,  # Return strings instead of bytes
        )
        
    return _redis_pool


def get_redis_client() -> redis.Redis:
    """
    Get a Redis client using the shared connection pool.
    
    Returns:
        redis.Redis: A Redis client instance.
        
    Example:
        client = get_redis_client()
        client.set("user:123:session", "active", ex=3600)
        is_active = client.get("user:123:session")
    """
    return redis.Redis(connection_pool=get_redis_pool())


def check_redis_connection() -> bool:
    """
    Check if Redis connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise.
    """
    try:
        client = get_redis_client()
        return client.ping()
    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Redis health check error: {e}")
        return False


def close_redis_pool() -> None:
    """
    Close the Redis connection pool. 
    Call this on application shutdown.
    """
    global _redis_pool
    
    if _redis_pool is not None:
        logger.info("Closing Redis connection pool")
        _redis_pool.disconnect()
        _redis_pool = None


# Cache helper functions for common patterns

def cache_get(key: str) -> Optional[str]:
    """Get a value from cache, returns None if not found."""
    try:
        return get_redis_client().get(key)
    except Exception as e:
        logger.warning(f"Cache get failed for {key}: {e}")
        return None


def cache_set(key: str, value: str, ttl_seconds: int = 3600) -> bool:
    """Set a value in cache with TTL. Returns True on success."""
    try:
        return get_redis_client().set(key, value, ex=ttl_seconds)
    except Exception as e:
        logger.warning(f"Cache set failed for {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete a key from cache. Returns True on success."""
    try:
        return get_redis_client().delete(key) > 0
    except Exception as e:
        logger.warning(f"Cache delete failed for {key}: {e}")
        return False
