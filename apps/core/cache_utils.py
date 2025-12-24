"""
Cache utility functions for common caching patterns.
"""
from django.core.cache import cache
from typing import Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)


def cache_result(key_prefix: str, timeout: int = 300):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key
        timeout: Cache timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def get_or_set_cache(key: str, callable_func: Callable, timeout: int = 300) -> Any:
    """
    Get value from cache or set it using callable.
    
    Args:
        key: Cache key
        callable_func: Function to call if cache miss
        timeout: Cache timeout in seconds
    
    Returns:
        Cached or computed value
    """
    value = cache.get(key)
    if value is None:
        value = callable_func()
        cache.set(key, value, timeout)
    return value


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate cache keys matching a pattern.
    Note: This is a simple implementation. For production, consider using
    django-redis with SCAN for pattern matching.
    
    Args:
        pattern: Cache key pattern to invalidate
    """
    # Simple implementation - in production, use Redis SCAN
    logger.warning(f"Cache invalidation for pattern '{pattern}' - implement with Redis SCAN in production")

