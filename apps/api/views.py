"""
System health and monitoring endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import connection, models
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


class CSDHealthView(APIView):
    """CSD connectivity health check endpoint."""
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["System"],
        summary="CSD connectivity check",
        description="Checks connectivity to Euroclear, Clearstream, and XETRA APIs.",
        responses={
            200: OpenApiResponse(
                description="CSD connectivity status",
                response={
                    "type": "object",
                    "properties": {
                        "euroclear": {"type": "string", "example": "connected"},
                        "clearstream": {"type": "string", "example": "connected"},
                        "xetra": {"type": "string", "example": "connected"}
                    }
                }
            )
        }
    )
    def get(self, request):
        """Check CSD connectivity."""
        import os
        checks = {
            'euroclear': 'unknown',
            'clearstream': 'unknown',
            'xetra': 'unknown'
        }
        
        # Check Euroclear
        euroclear_base = os.getenv('EUROCLEAR_API_BASE', '')
        euroclear_key = os.getenv('EUROCLEAR_API_KEY', '')
        if euroclear_base and euroclear_key:
            if not euroclear_base.endswith('.example'):
                checks['euroclear'] = 'configured'
                # Try a simple connectivity test
                try:
                    from apps.euroclear.client import EuroclearClient
                    client = EuroclearClient()
                    # Just check if client initializes properly
                    checks['euroclear'] = 'ready'
                except Exception as e:
                    logger.warning(f"Euroclear client check failed: {str(e)}")
                    checks['euroclear'] = 'error'
            else:
                checks['euroclear'] = 'development_mode'
        else:
            checks['euroclear'] = 'not_configured'
        
        # Check Clearstream
        clearstream_base = os.getenv('CLEARSTREAM_PMI_BASE', '')
        clearstream_key = os.getenv('CLEARSTREAM_PMI_KEY', '')
        if clearstream_base and clearstream_key:
            if not clearstream_base.endswith('.example'):
                checks['clearstream'] = 'configured'
                try:
                    from apps.clearstream.client import ClearstreamClient
                    client = ClearstreamClient()
                    checks['clearstream'] = 'ready'
                except Exception as e:
                    logger.warning(f"Clearstream client check failed: {str(e)}")
                    checks['clearstream'] = 'error'
            else:
                checks['clearstream'] = 'development_mode'
        else:
            checks['clearstream'] = 'not_configured'
        
        # Check XETRA
        xetra_base = os.getenv('XETRA_API_BASE', '')
        xetra_key = os.getenv('XETRA_API_KEY', '')
        if xetra_base and xetra_key:
            if not xetra_base.endswith('.example'):
                checks['xetra'] = 'configured'
                try:
                    from apps.xetra.client import XetraClient
                    client = XetraClient()
                    checks['xetra'] = 'ready'
                except Exception as e:
                    logger.warning(f"XETRA client check failed: {str(e)}")
                    checks['xetra'] = 'error'
            else:
                checks['xetra'] = 'development_mode'
        else:
            checks['xetra'] = 'not_configured'
        
        return Response(checks, status=200)


class RedirectConfigView(APIView):
    """Expose redirect config for quick validation."""

    def get_permissions(self):
        if getattr(settings, 'REDIRECT_STATS_PUBLIC', False):
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["System"],
        summary="Redirect configuration",
        description="Returns current CTA redirect base URL and route map.",
        responses={200: OpenApiResponse(description="Redirect configuration")},
    )
    def get(self, request):
        return Response({
            'base_url': getattr(settings, 'PAYBITO_BASE_URL', ''),
            'routes': getattr(settings, 'CTA_REDIRECT_ROUTES', {}),
        })


class RedirectStatsView(APIView):
    """Basic redirect stats for GTM validation."""

    def get_permissions(self):
        if getattr(settings, 'REDIRECT_STATS_PUBLIC', False):
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["System"],
        summary="Redirect stats",
        description="Returns redirect counts by route and recent activity.",
        responses={200: OpenApiResponse(description="Redirect stats")},
    )
    def get(self, request):
        from apps.core.models import RedirectEvent
        from django.utils import timezone
        from datetime import timedelta
        from django.db.utils import OperationalError, ProgrammingError

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_1h = now - timedelta(hours=1)

        try:
            total = RedirectEvent.objects.count()
            total_24h = RedirectEvent.objects.filter(created_at__gte=last_24h).count()
            total_1h = RedirectEvent.objects.filter(created_at__gte=last_1h).count()

            per_route = (
                RedirectEvent.objects
                .values('route')
                .order_by('route')
                .annotate(count=models.Count('id'))
            )
            per_route_list = list(per_route)
            status = "ok"
        except (OperationalError, ProgrammingError) as exc:
            logger.warning("Redirect stats unavailable (DB not ready): %s", exc)
            total = total_24h = total_1h = 0
            per_route_list = []
            status = "db_not_ready"

        return Response({
            'timestamp': now.isoformat(),
            'status': status,
            'total': total,
            'last_24h': total_24h,
            'last_1h': total_1h,
            'per_route': per_route_list,
        })
