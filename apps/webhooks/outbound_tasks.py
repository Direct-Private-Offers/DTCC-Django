"""
Celery tasks for outbound webhook delivery.
"""
from celery import shared_task
from django.utils import timezone
from .models import OutboundWebhook, OutboundWebhookDelivery
from .outbound import get_webhook_service
import logging

logger = logging.getLogger(__name__)


@shared_task
def deliver_webhook_task(webhook_id: str, event_type: str, payload: dict):
    """
    Deliver a webhook asynchronously.
    
    Args:
        webhook_id: OutboundWebhook UUID
        event_type: Event type
        payload: Webhook payload
    """
    try:
        webhook = OutboundWebhook.objects.get(id=webhook_id, status=OutboundWebhook.Status.ACTIVE)
        
        # Check if webhook subscribes to this event
        if event_type not in webhook.events:
            logger.debug(f"Webhook {webhook_id} does not subscribe to event {event_type}")
            return
        
        service = get_webhook_service()
        delivery = service.deliver_webhook(webhook, event_type, payload)
        
        logger.info(f"Webhook delivery {delivery.id} completed with status {delivery.status}")
    
    except OutboundWebhook.DoesNotExist:
        logger.error(f"Webhook {webhook_id} not found")
    except Exception as e:
        logger.error(f"Error delivering webhook {webhook_id}: {str(e)}", exc_info=True)


@shared_task
def retry_failed_webhooks():
    """
    Retry failed webhook deliveries.
    Runs periodically to retry failed deliveries.
    """
    failed_deliveries = OutboundWebhookDelivery.objects.filter(
        status=OutboundWebhookDelivery.Status.FAILED,
        retry_count__lt=3,  # Max retries
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)  # Only retry recent failures
    )
    
    service = get_webhook_service()
    retried = 0
    
    for delivery in failed_deliveries[:100]:  # Limit to 100 per run
        try:
            service.retry_failed_delivery(delivery)
            retried += 1
        except Exception as e:
            logger.error(f"Error retrying webhook delivery {delivery.id}: {str(e)}")
    
    logger.info(f"Retried {retried} failed webhook deliveries")


def trigger_webhook_event(event_type: str, payload: dict):
    """
    Trigger webhook event for all active subscribers.
    
    Args:
        event_type: Event type (e.g., 'order.filled', 'settlement.complete')
        payload: Event payload
    """
    active_webhooks = OutboundWebhook.objects.filter(
        status=OutboundWebhook.Status.ACTIVE
    )
    
    for webhook in active_webhooks:
        if event_type in webhook.events:
            deliver_webhook_task.delay(str(webhook.id), event_type, payload)

