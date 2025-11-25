from django.db import models


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=128)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=256)
    response = models.JSONField()
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ("key", "path")


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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"WebhookReplay(nonce={self.nonce})"
