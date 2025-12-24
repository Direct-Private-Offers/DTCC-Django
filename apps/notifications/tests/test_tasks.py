"""
Tests for notification tasks.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.tasks import send_notification, _send_email


class TestNotificationTasks:
    """Test notification Celery tasks."""
    
    @pytest.fixture
    def test_user(self, db):
        """Create a test user."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def test_notification(self, test_user):
        """Create a test notification."""
        return Notification.objects.create(
            user=test_user,
            notification_type='EMAIL',
            recipient='test@example.com',
            subject='Test Subject',
            body='Test body content',
            status=Notification.Status.PENDING
        )
    
    @patch('apps.notifications.tasks.sendgrid.SendGridAPIClient')
    def test_send_email_with_sendgrid(self, mock_sendgrid_client, test_notification, settings):
        """Test email sending with SendGrid."""
        settings.SENDGRID_API_KEY = 'test-api-key'
        settings.SENDGRID_FROM_EMAIL = 'noreply@test.com'
        settings.SENDGRID_FROM_NAME = 'Test App'
        
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.body = b'{"message": "success"}'
        
        mock_sg = MagicMock()
        mock_sg.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_sg
        
        _send_email(test_notification)
        
        # Verify SendGrid was called
        mock_sendgrid_client.assert_called_once_with(api_key='test-api-key')
        mock_sg.send.assert_called_once()
        
        # Verify notification status updated
        test_notification.refresh_from_db()
        assert test_notification.status == Notification.Status.SENT
        assert test_notification.sent_at is not None
    
    @patch('apps.notifications.tasks.send_mail')
    def test_send_email_fallback(self, mock_send_mail, test_notification, settings):
        """Test email sending fallback to Django send_mail."""
        settings.SENDGRID_API_KEY = ''  # No SendGrid key
        
        _send_email(test_notification)
        
        # Verify Django send_mail was called
        mock_send_mail.assert_called_once_with(
            subject='Test Subject',
            message='Test body content',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        
        # Verify notification status updated
        test_notification.refresh_from_db()
        assert test_notification.status == Notification.Status.SENT
    
    def test_send_notification_respects_user_preferences(self, test_user, db):
        """Test that notifications respect user preferences."""
        # Create notification preference disabling email
        NotificationPreference.objects.create(
            user=test_user,
            email_enabled=False
        )
        
        notification = Notification.objects.create(
            user=test_user,
            notification_type='EMAIL',
            recipient='test@example.com',
            subject='Test',
            body='Test',
            status=Notification.Status.PENDING
        )
        
        send_notification(str(notification.id))
        
        notification.refresh_from_db()
        assert notification.status == Notification.Status.FAILED
        assert 'disabled by user' in notification.error_message

