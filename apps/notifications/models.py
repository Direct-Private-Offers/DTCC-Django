"""
Notification models for email, SMS, and in-app notifications.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


class NotificationTemplate(models.Model):
    """Notification templates for different event types."""
    class NotificationType(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        IN_APP = 'IN_APP', 'In-App'
        WEBHOOK = 'WEBHOOK', 'Webhook'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    notification_type = models.CharField(max_length=16, choices=NotificationType.choices)
    event_type = models.CharField(max_length=64, db_index=True)  # ORDER_FILLED, SETTLEMENT_COMPLETE, etc.
    subject = models.CharField(max_length=256, null=True, blank=True)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_templates'
        indexes = [
            models.Index(fields=['event_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"NotificationTemplate({self.name}, {self.notification_type})"


class Notification(models.Model):
    """Notification records."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'
        DELIVERED = 'DELIVERED', 'Delivered'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    notification_type = models.CharField(max_length=16)
    recipient = models.CharField(max_length=256)  # Email, phone, or user ID
    subject = models.CharField(max_length=256, null=True, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification({self.notification_type}, {self.status}, {self.user.username})"


class NotificationPreference(models.Model):
    """User notification preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)
    webhook_enabled = models.BooleanField(default=False)
    webhook_url = models.URLField(null=True, blank=True)
    preferences = models.JSONField(default=dict)  # Per-event preferences
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_preferences'
    
    def __str__(self):
        return f"NotificationPreference({self.user.username})"

