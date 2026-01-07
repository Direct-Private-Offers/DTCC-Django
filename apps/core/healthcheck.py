"""
Healthcheck endpoint for DTCC Django MVP
Simple status check to verify API is running and can connect to dependencies
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


def healthcheck(request):
    """
    Basic healthcheck endpoint - returns 200 OK if API is operational.
    
    GET /api/health
    
    Response:
    {
        "status": "ok",
        "timestamp": "2025-12-27T12:00:00Z",
        "database": "ok",
        "mock_mode": true,
        "version": "1.0.0"
    }
    """
    from datetime import datetime
    
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "version": "1.0.0",
    }
    
    # Check database connection
    try:
        connection.ensure_connection()
        health_status["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "error"
        health_status["status"] = "degraded"
    
    # Check if running in mock mode (for external APIs)
    euroclear_key = os.getenv('EUROCLEAR_API_KEY', 'test-key')
    clearstream_key = os.getenv('CLEARSTREAM_PMI_KEY', '')
    
    health_status["mock_mode"] = {
        "euroclear": euroclear_key in ['test-key', ''] or euroclear_key.startswith('mock-'),
        "clearstream": not clearstream_key or clearstream_key.startswith('mock-'),
    }
    
    # Check Redis (if configured)
    try:
        from django.core.cache import cache
        cache.set('healthcheck', 'ok', 1)
        redis_check = cache.get('healthcheck') == 'ok'
        health_status["redis"] = "ok" if redis_check else "error"
    except Exception as e:
        logger.warning(f"Redis health check failed (optional): {e}")
        health_status["redis"] = "not_configured"
    
    status_code = 200 if health_status["status"] == "ok" else 503
    return JsonResponse(health_status, status=status_code)
