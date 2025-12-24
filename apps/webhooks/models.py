"""
Webhook models for inbound and outbound webhooks.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


class WebhookEvent(models.Model):
    """Incoming webhook events from external services."""
    class Source(models.TextChoices):
        EUROCLEAR = 'euroclear', 'Euroclear'
        CLEARSTREAM = 'clearstream', 'Clearstream'
        CHAINLINK = 'chainlink', 'Chainlink'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        PROCESSED = 'PROCESSED', 'Processed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=16, choices=Source.choices)
    event_type = models.CharField(max_length=64)
    event_data = models.JSONField()
    reference = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhooks_events'
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"WebhookEvent({self.source}, {self.event_type}, {self.status})"


class WebhookReplay(models.Model):
    """Stores seen webhook nonces to prevent replay for a short window."""
    nonce = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'webhooks_replay'
        indexes = [
            models.Index(fields=['created_at']),
        ]


class OutboundWebhook(models.Model):
    """Outbound webhook subscriptions."""
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        SUSPENDED = 'SUSPENDED', 'Suspended'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outbound_webhooks')
    url = models.URLField(max_length=512)
    secret = models.CharField(max_length=128)  # For HMAC signature generation
    events = models.JSONField(default=list)  # List of event types to subscribe to
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'webhooks_outbound'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"OutboundWebhook({self.user.username}, {self.url})"


class OutboundWebhookDelivery(models.Model):
    """Outbound webhook delivery records."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        EXHAUSTED = 'EXHAUSTED', 'Exhausted'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(OutboundWebhook, on_delete=models.CASCADE, related_name='deliveries')
    event_type = models.CharField(max_length=64)
    payload = models.JSONField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'webhooks_outbound_deliveries'
        indexes = [
            models.Index(fields=['webhook', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['event_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OutboundWebhookDelivery({self.event_type}, {self.status})"

