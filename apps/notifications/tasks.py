"""
Celery tasks for sending notifications.
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification, NotificationPreference
import logging
import sendgrid
from sendgrid.helpers.mail import Mail, Email, Content

logger = logging.getLogger(__name__)


@shared_task
def send_notification(notification_id: str):
    """
    Send a notification asynchronously.
    
    Args:
        notification_id: Notification UUID
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.status != Notification.Status.PENDING:
            logger.warning(f"Notification {notification_id} is not pending")
            return
        
        # Check user preferences
        try:
            prefs = notification.user.notification_preferences
            if notification.notification_type == 'EMAIL' and not prefs.email_enabled:
                notification.status = Notification.Status.FAILED
                notification.error_message = "Email notifications disabled by user"
                notification.save()
                return
            if notification.notification_type == 'SMS' and not prefs.sms_enabled:
                notification.status = Notification.Status.FAILED
                notification.error_message = "SMS notifications disabled by user"
                notification.save()
                return
        except NotificationPreference.DoesNotExist:
            pass  # Use defaults
        
        # Send based on type
        if notification.notification_type == 'EMAIL':
            _send_email(notification)
        elif notification.notification_type == 'SMS':
            _send_sms(notification)
        elif notification.notification_type == 'WEBHOOK':
            _send_webhook(notification)
        else:
            # In-app notifications are stored but not "sent"
            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()
            notification.save()
    
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {str(e)}")
        if notification:
            notification.status = Notification.Status.FAILED
            notification.error_message = str(e)
            notification.save()


def _send_email(notification: Notification):
    """Send email notification via SendGrid."""
    try:
        # Use SendGrid API directly if API key is configured
        if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            
            from_email = Email(
                settings.SENDGRID_FROM_EMAIL,
                settings.SENDGRID_FROM_NAME
            )
            to_email = Email(notification.recipient)
            subject = notification.subject or 'Notification'
            content = Content("text/html", notification.body)
            
            mail = Mail(from_email, to_email, subject, content)
            
            response = sg.send(mail)
            
            # Log SendGrid response
            if response.status_code in [200, 202]:
                notification.status = Notification.Status.SENT
                notification.sent_at = timezone.now()
                notification.save()
                logger.info(f"Email sent via SendGrid to {notification.recipient}, status: {response.status_code}")
            else:
                raise Exception(f"SendGrid returned status {response.status_code}: {response.body}")
        else:
            # Fallback to Django's send_mail (uses configured backend)
            send_mail(
                subject=notification.subject or 'Notification',
                message=notification.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient],
                fail_silently=False,
            )
            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()
            notification.save()
            logger.info(f"Email sent via Django backend to {notification.recipient}")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise


def _send_sms(notification: Notification):
    """Send SMS notification."""
    # TODO: Integrate with SMS provider (Twilio, AWS SNS, etc.)
    logger.warning("SMS sending not implemented")
    notification.status = Notification.Status.FAILED
    notification.error_message = "SMS provider not configured"
    notification.save()


def _send_webhook(notification: Notification):
    """Send webhook notification."""
    # TODO: Implement webhook delivery
    logger.warning("Webhook sending not implemented")
    notification.status = Notification.Status.FAILED
    notification.error_message = "Webhook delivery not implemented"
    notification.save()

