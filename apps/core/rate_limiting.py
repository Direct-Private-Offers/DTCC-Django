"""
Enhanced rate limiting utilities.
"""
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with sliding window algorithm."""
    
    def __init__(self, key_func: Callable, rate: str, cache_key_prefix: str = 'ratelimit'):
        """
        Initialize rate limiter.
        
        Args:
            key_func: Function to generate cache key from request
            rate: Rate limit string (e.g., '10/m', '100/h')
            cache_key_prefix: Prefix for cache keys
        """
        self.key_func = key_func
        self.rate = rate
        self.cache_key_prefix = cache_key_prefix
        self.limit, self.period = self._parse_rate(rate)
    
    def _parse_rate(self, rate: str) -> tuple:
        """Parse rate string into limit and period."""
        parts = rate.split('/')
        limit = int(parts[0])
        period_str = parts[1].lower()
        
        period_map = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
        }
        
        period = period_map.get(period_str, 60)
        return limit, period
    
    def is_allowed(self, request) -> tuple[bool, dict]:
        """
        Check if request is allowed.
        
        Returns:
            (is_allowed, info_dict)
        """
        key = f"{self.cache_key_prefix}:{self.key_func(request)}"
        now = timezone.now().timestamp()
        
        # Get current window
        window_start = int(now // self.period) * self.period
        cache_key = f"{key}:{window_start}"
        
        # Get current count
        count = cache.get(cache_key, 0)
        
        if count >= self.limit:
            return False, {
                'limit': self.limit,
                'remaining': 0,
                'reset': window_start + self.period,
            }
        
        # Increment count
        cache.set(cache_key, count + 1, self.period)
        
        return True, {
            'limit': self.limit,
            'remaining': self.limit - count - 1,
            'reset': window_start + self.period,
        }


def rate_limit(key_func: Callable, rate: str, cache_key_prefix: str = 'ratelimit'):
    """
    Decorator for rate limiting.
    
    Args:
        key_func: Function to generate cache key from request
        rate: Rate limit string (e.g., '10/m', '100/h')
        cache_key_prefix: Prefix for cache keys
    
    Example:
        @rate_limit(lambda r: f"user:{r.user.id}", '10/m')
        def my_view(request):
            ...
    """
    limiter = RateLimiter(key_func, rate, cache_key_prefix)
    
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            is_allowed, info = limiter.is_allowed(request)
            
            if not is_allowed:
                response = JsonResponse({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'limit': info['limit'],
                    'reset': info['reset'],
                }, status=429)
                response['X-RateLimit-Limit'] = str(info['limit'])
                response['X-RateLimit-Remaining'] = '0'
                response['X-RateLimit-Reset'] = str(info['reset'])
                return response
            
            # Add rate limit headers
            response = view_func(request, *args, **kwargs)
            if hasattr(response, 'headers'):
                response['X-RateLimit-Limit'] = str(info['limit'])
                response['X-RateLimit-Remaining'] = str(info['remaining'])
                response['X-RateLimit-Reset'] = str(info['reset'])
            return response
        
        return _wrapped
    return decorator


def get_user_key(request) -> str:
    """Get rate limit key for authenticated user."""
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    return f"ip:{request.META.get('REMOTE_ADDR', 'unknown')}"


def get_endpoint_key(request) -> str:
    """Get rate limit key for endpoint."""
    return f"endpoint:{request.path}:{request.method}"

