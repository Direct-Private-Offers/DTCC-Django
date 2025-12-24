"""
Outbound webhook delivery system.
"""
import hmac
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.conf import settings
import httpx
from .models import OutboundWebhook, OutboundWebhookDelivery

logger = logging.getLogger(__name__)


class WebhookDeliveryService:
    """Service for delivering outbound webhooks."""
    
    def __init__(self):
        self.timeout = 30  # seconds
        self.max_retries = 3
    
    def deliver_webhook(
        self,
        webhook: OutboundWebhook,
        event_type: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> OutboundWebhookDelivery:
        """
        Deliver a webhook to the subscriber.
        
        Args:
            webhook: OutboundWebhook instance
            event_type: Event type (e.g., 'order.filled', 'settlement.complete')
            payload: Webhook payload data
            headers: Additional headers to include
        
        Returns:
            OutboundWebhookDelivery instance
        """
        # Create delivery record
        delivery = OutboundWebhookDelivery.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload=payload,
            status=OutboundWebhookDelivery.Status.PENDING
        )
        
        # Generate signature
        signature = self._generate_signature(payload, webhook.secret)
        
        # Prepare headers
        request_headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': event_type,
            'X-Webhook-Signature': f'sha256={signature}',
            'X-Webhook-Timestamp': str(int(timezone.now().timestamp())),
            'X-Webhook-Id': str(delivery.id),
        }
        
        if headers:
            request_headers.update(headers)
        
        # Attempt delivery
        try:
            response = httpx.post(
                webhook.url,
                json=payload,
                headers=request_headers,
                timeout=self.timeout,
            )
            
            delivery.status_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response size
            
            if 200 <= response.status_code < 300:
                delivery.status = OutboundWebhookDelivery.Status.SUCCESS
                delivery.delivered_at = timezone.now()
                logger.info(f"Webhook {delivery.id} delivered successfully to {webhook.url}")
            else:
                delivery.status = OutboundWebhookDelivery.Status.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"Webhook {delivery.id} failed with status {response.status_code}")
        
        except httpx.TimeoutException:
            delivery.status = OutboundWebhookDelivery.Status.FAILED
            delivery.error_message = "Request timeout"
            logger.error(f"Webhook {delivery.id} timed out")
        
        except httpx.RequestError as e:
            delivery.status = OutboundWebhookDelivery.Status.FAILED
            delivery.error_message = str(e)
            logger.error(f"Webhook {delivery.id} request error: {str(e)}")
        
        except Exception as e:
            delivery.status = OutboundWebhookDelivery.Status.FAILED
            delivery.error_message = str(e)
            logger.error(f"Webhook {delivery.id} unexpected error: {str(e)}")
        
        delivery.save()
        return delivery
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC SHA256 signature for webhook payload.
        
        Args:
            payload: Webhook payload
            secret: Webhook secret
        
        Returns:
            Hex signature string
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def retry_failed_delivery(self, delivery: OutboundWebhookDelivery) -> OutboundWebhookDelivery:
        """
        Retry a failed webhook delivery.
        
        Args:
            delivery: Failed OutboundWebhookDelivery instance
        
        Returns:
            Updated delivery instance
        """
        if delivery.retry_count >= self.max_retries:
            delivery.status = OutboundWebhookDelivery.Status.EXHAUSTED
            delivery.save()
            logger.warning(f"Webhook {delivery.id} exhausted retries")
            return delivery
        
        delivery.retry_count += 1
        delivery.status = OutboundWebhookDelivery.Status.PENDING
        delivery.save()
        
        # Re-deliver
        return self.deliver_webhook(
            delivery.webhook,
            delivery.event_type,
            delivery.payload
        )


def get_webhook_service() -> WebhookDeliveryService:
    """Get webhook delivery service instance."""
    return WebhookDeliveryService()

