"""
Notification API views.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from apps.core.responses import ok, bad_request
from .models import Notification, NotificationPreference
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.core.schemas import ERROR_401


class NotificationView(APIView):
    """User notifications."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Notifications"],
        summary="List notifications",
        description="Get notifications for authenticated user.",
        responses={200: OpenApiResponse(description="List of notifications")}
    )
    def get(self, request: Request):
        """List user notifications."""
        status_filter = request.query_params.get('status')
        notifications = Notification.objects.filter(user=request.user)
        
        if status_filter:
            notifications = notifications.filter(status=status_filter)
        
        notifications = notifications.order_by('-created_at')[:50]
        
        return ok({
            'notifications': [
                {
                    'id': str(n.id),
                    'type': n.notification_type,
                    'subject': n.subject,
                    'body': n.body,
                    'status': n.status,
                    'created_at': n.created_at.isoformat(),
                    'sent_at': n.sent_at.isoformat() if n.sent_at else None,
                }
                for n in notifications
            ]
        })


class NotificationPreferenceView(APIView):
    """Notification preferences management."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Notifications"],
        summary="Get notification preferences",
        description="Get notification preferences for authenticated user.",
        responses={200: OpenApiResponse(description="Notification preferences")}
    )
    def get(self, request: Request):
        """Get notification preferences."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return ok({
            'email_enabled': prefs.email_enabled,
            'sms_enabled': prefs.sms_enabled,
            'in_app_enabled': prefs.in_app_enabled,
            'webhook_enabled': prefs.webhook_enabled,
            'webhook_url': prefs.webhook_url,
        })
    
    @extend_schema(
        tags=["Notifications"],
        summary="Update notification preferences",
        description="Update notification preferences for authenticated user.",
        responses={200: OpenApiResponse(description="Preferences updated")}
    )
    def patch(self, request: Request):
        """Update notification preferences."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        
        if 'email_enabled' in request.data:
            prefs.email_enabled = request.data['email_enabled']
        if 'sms_enabled' in request.data:
            prefs.sms_enabled = request.data['sms_enabled']
        if 'in_app_enabled' in request.data:
            prefs.in_app_enabled = request.data['in_app_enabled']
        if 'webhook_enabled' in request.data:
            prefs.webhook_enabled = request.data['webhook_enabled']
        if 'webhook_url' in request.data:
            prefs.webhook_url = request.data['webhook_url']
        
        prefs.save()
        
        return ok({
            'email_enabled': prefs.email_enabled,
            'sms_enabled': prefs.sms_enabled,
            'in_app_enabled': prefs.in_app_enabled,
            'webhook_enabled': prefs.webhook_enabled,
            'webhook_url': prefs.webhook_url,
        })

