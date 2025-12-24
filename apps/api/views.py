"""
System health and monitoring endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from apps.core.responses import ok
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

logger = logging.getLogger(__name__)


class HealthView(APIView):
    """Basic health check endpoint."""
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["System"],
        summary="Health check",
        description="Basic health check endpoint. Returns 200 if service is running.",
        responses={
            200: OpenApiResponse(
                description="Service is healthy",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "healthy"},
                        "timestamp": {"type": "string"}
                    }
                }
            )
        }
    )
    def get(self, request):
        """Return health status."""
        return ok({
            'status': 'healthy',
            'service': 'DTCC STO Backend API',
            'version': '1.0.0'
        })


class ReadinessView(APIView):
    """Readiness check endpoint - verifies dependencies."""
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["System"],
        summary="Readiness check",
        description="Checks if service dependencies (database, cache) are available.",
        responses={
            200: OpenApiResponse(
                description="Service is ready",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "ready"},
                        "database": {"type": "string", "example": "connected"},
                        "cache": {"type": "string", "example": "connected"}
                    }
                }
            ),
            503: OpenApiResponse(description="Service is not ready")
        }
    )
    def get(self, request):
        """Check service readiness."""
        checks = {
            'status': 'ready',
            'database': 'unknown',
            'cache': 'unknown'
        }
        status_code = 200
        
        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks['database'] = 'connected'
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            checks['database'] = 'disconnected'
            status_code = 503
        
        # Check cache
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                checks['cache'] = 'connected'
            else:
                checks['cache'] = 'disconnected'
                status_code = 503
        except Exception as e:
            logger.error(f"Cache check failed: {str(e)}")
            checks['cache'] = 'disconnected'
            status_code = 503
        
        return Response(checks, status=status_code)


class MetricsView(APIView):
    """Metrics endpoint for monitoring."""
    permission_classes = [AllowAny]  # Can be restricted in production
    
    @extend_schema(
        tags=["System"],
        summary="System metrics",
        description="Returns system metrics for monitoring (Prometheus format).",
        responses={
            200: OpenApiResponse(description="Metrics data")
        }
    )
    def get(self, request):
        """Return system metrics."""
        from apps.core.models import ApiSession, IdempotencyKey, WebhookEvent
        from django.utils import timezone
        from datetime import timedelta
        
        metrics = {
            'timestamp': timezone.now().isoformat(),
            'active_sessions': ApiSession.objects.filter(
                last_seen__gte=timezone.now() - timedelta(hours=1)
            ).count(),
            'total_idempotency_keys': IdempotencyKey.objects.filter(
                expires_at__gt=timezone.now()
            ).count(),
            'pending_webhook_events': WebhookEvent.objects.filter(
                status='PENDING'
            ).count(),
        }
        
        return Response(metrics, status=200)

