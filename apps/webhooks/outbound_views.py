"""
Views for outbound webhook management.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django.shortcuts import get_object_or_404
from apps.core.responses import ok, bad_request, not_found
from apps.core.idempotency import idempotent
from .models import OutboundWebhook, OutboundWebhookDelivery
from .outbound import get_webhook_service
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_404
import secrets
import logging

logger = logging.getLogger(__name__)


class OutboundWebhookView(APIView):
    """Outbound webhook subscription management."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Webhooks"],
        summary="List outbound webhooks",
        description="List all outbound webhook subscriptions for authenticated user.",
        responses={200: OpenApiResponse(description="List of webhooks")}
    )
    def get(self, request: Request):
        """List user's webhook subscriptions."""
        webhooks = OutboundWebhook.objects.filter(user=request.user)
        return ok({
            'webhooks': [
                {
                    'id': str(w.id),
                    'url': w.url,
                    'events': w.events,
                    'status': w.status,
                    'description': w.description,
                    'created_at': w.created_at.isoformat(),
                }
                for w in webhooks
            ]
        })
    
    @extend_schema(
        tags=["Webhooks"],
        summary="Create outbound webhook",
        description="Create a new outbound webhook subscription.",
        responses={200: OpenApiResponse(description="Webhook created")}
    )
    @idempotent
    def post(self, request: Request):
        """Create webhook subscription."""
        url = request.data.get('url')
        events = request.data.get('events', [])
        description = request.data.get('description')
        
        if not url:
            return bad_request("url is required")
        
        if not isinstance(events, list) or not events:
            return bad_request("events must be a non-empty list")
        
        # Generate secret
        secret = secrets.token_urlsafe(32)
        
        webhook = OutboundWebhook.objects.create(
            user=request.user,
            url=url,
            secret=secret,
            events=events,
            description=description,
        )
        
        return ok({
            'id': str(webhook.id),
            'url': webhook.url,
            'events': webhook.events,
            'status': webhook.status,
            'secret': secret,  # Only returned on creation
            'created_at': webhook.created_at.isoformat(),
        })
    
    @extend_schema(
        tags=["Webhooks"],
        summary="Update outbound webhook",
        description="Update an existing webhook subscription.",
        responses={200: OpenApiResponse(description="Webhook updated")}
    )
    @idempotent
    def patch(self, request: Request, webhook_id: str):
        """Update webhook subscription."""
        webhook = get_object_or_404(OutboundWebhook, id=webhook_id, user=request.user)
        
        if 'url' in request.data:
            webhook.url = request.data['url']
        if 'events' in request.data:
            webhook.events = request.data['events']
        if 'status' in request.data:
            webhook.status = request.data['status']
        if 'description' in request.data:
            webhook.description = request.data['description']
        
        webhook.save()
        
        return ok({
            'id': str(webhook.id),
            'url': webhook.url,
            'events': webhook.events,
            'status': webhook.status,
            'updated_at': webhook.updated_at.isoformat(),
        })
    
    @extend_schema(
        tags=["Webhooks"],
        summary="Delete outbound webhook",
        description="Delete a webhook subscription.",
        responses={200: OpenApiResponse(description="Webhook deleted")}
    )
    def delete(self, request: Request, webhook_id: str):
        """Delete webhook subscription."""
        webhook = get_object_or_404(OutboundWebhook, id=webhook_id, user=request.user)
        webhook.delete()
        return ok({'message': 'Webhook deleted'})


class OutboundWebhookDeliveryView(APIView):
    """Outbound webhook delivery history."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Webhooks"],
        summary="List webhook deliveries",
        description="List delivery history for a webhook.",
        responses={200: OpenApiResponse(description="List of deliveries")}
    )
    def get(self, request: Request, webhook_id: str):
        """List webhook delivery history."""
        webhook = get_object_or_404(OutboundWebhook, id=webhook_id, user=request.user)
        
        deliveries = OutboundWebhookDelivery.objects.filter(webhook=webhook)[:50]
        
        return ok({
            'deliveries': [
                {
                    'id': str(d.id),
                    'event_type': d.event_type,
                    'status': d.status,
                    'status_code': d.status_code,
                    'retry_count': d.retry_count,
                    'delivered_at': d.delivered_at.isoformat() if d.delivered_at else None,
                    'created_at': d.created_at.isoformat(),
                    'error_message': d.error_message,
                }
                for d in deliveries
            ]
        })


class OutboundWebhookRetryView(APIView):
    """Retry failed webhook delivery."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Webhooks"],
        summary="Retry webhook delivery",
        description="Retry a failed webhook delivery.",
        responses={200: OpenApiResponse(description="Delivery retried")}
    )
    def post(self, request: Request, delivery_id: str):
        """Retry failed delivery."""
        delivery = get_object_or_404(OutboundWebhookDelivery, id=delivery_id)
        
        # Verify user owns the webhook
        if delivery.webhook.user != request.user:
            return not_found("Delivery not found")
        
        service = get_webhook_service()
        updated_delivery = service.retry_failed_delivery(delivery)
        
        return ok({
            'id': str(updated_delivery.id),
            'status': updated_delivery.status,
            'retry_count': updated_delivery.retry_count,
        })

