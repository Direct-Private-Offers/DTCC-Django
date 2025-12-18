from django.db import models
import uuid


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=128)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=256)
    response = models.JSONField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        unique_together = ("key", "path")
        indexes = [
            models.Index(fields=['expires_at']),
        ]


class ApiSession(models.Model):
    """Lightweight session/activity tracker keyed by JWT jti when available."""
    jti = models.CharField(max_length=64, db_index=True)
    subject = models.CharField(max_length=128, db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"ApiSession(jti={self.jti}, subject={self.subject})"


class WebhookReplay(models.Model):
    """Stores seen webhook nonces to prevent replay for a short window."""
    nonce = models.CharField(max_length=128, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"WebhookReplay(nonce={self.nonce})"


class WebhookEvent(models.Model):
    """Stores webhook events for async processing."""
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
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"WebhookEvent({self.source}, {self.event_type}, {self.status})"
