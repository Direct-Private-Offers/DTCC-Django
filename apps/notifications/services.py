"""
Notification service for creating and sending notifications.
"""
import logging
from typing import Optional, Dict, Any
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Notification, NotificationTemplate, NotificationPreference
from .tasks import send_notification

logger = logging.getLogger(__name__)


def create_notification(
    user: User,
    event_type: str,
    notification_type: str = 'EMAIL',
    context: Optional[Dict[str, Any]] = None,
    recipient: Optional[str] = None
) -> Notification:
    """
    Create and queue a notification.
    
    Args:
        user: User to notify
        event_type: Event type (ORDER_FILLED, SETTLEMENT_COMPLETE, etc.)
        notification_type: Type of notification (EMAIL, SMS, IN_APP, WEBHOOK)
        context: Template context variables
        recipient: Override recipient (defaults to user email)
    
    Returns:
        Created Notification instance
    """
    context = context or {}
    
    # Get template
    template = NotificationTemplate.objects.filter(
        event_type=event_type,
        notification_type=notification_type,
        is_active=True
    ).first()
    
    # Prepare notification
    subject = template.subject if template else f"Notification: {event_type}"
    body = template.body_template.format(**context) if template else f"Event: {event_type}"
    
    if not recipient:
        if notification_type == 'EMAIL':
            recipient = user.email
        elif notification_type == 'SMS':
            # Get from user profile if available
            recipient = getattr(user, 'phone_number', None) or ''
        else:
            recipient = str(user.id)
    
    notification = Notification.objects.create(
        user=user,
        template=template,
        notification_type=notification_type,
        recipient=recipient,
        subject=subject,
        body=body,
        metadata={'event_type': event_type, 'context': context}
    )
    
    # Queue for sending
    send_notification.delay(str(notification.id))
    
    logger.info(f"Created notification {notification.id} for user {user.username}")
    return notification


def notify_order_filled(user: User, order_id: str, isin: str, quantity: str):
    """Notify user when order is filled."""
    create_notification(
        user=user,
        event_type='ORDER_FILLED',
        notification_type='EMAIL',
        context={
            'order_id': order_id,
            'isin': isin,
            'quantity': quantity,
        }
    )


def notify_settlement_complete(user: User, settlement_id: str, isin: str):
    """Notify user when settlement is complete."""
    create_notification(
        user=user,
        event_type='SETTLEMENT_COMPLETE',
        notification_type='EMAIL',
        context={
            'settlement_id': settlement_id,
            'isin': isin,
        }
    )


def notify_kyc_approved(user: User):
    """Notify user when KYC is approved."""
    create_notification(
        user=user,
        event_type='KYC_APPROVED',
        notification_type='EMAIL',
        context={}
    )

