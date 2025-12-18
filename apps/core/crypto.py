import hmac
import hashlib
import os
from datetime import datetime, timezone
from typing import Optional
from django.utils import timezone as dj_timezone
from .models import WebhookReplay


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Support integer epoch seconds
        if value.isdigit():
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        # Fallback: ISO 8601
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        return None


def verify_hmac(request) -> bool:
    """
    Verify HMAC SHA256 signature of the raw request body using WEBHOOK_SECRET.
    Required headers:
      - X-Signature: sha256=<hex>
      - X-Timestamp: epoch seconds or ISO8601 (max skew 300s)
      - X-Nonce: unique string per event (prevents replay for a short window)
    """
    secret = os.getenv('WEBHOOK_SECRET') or os.getenv('API_HMAC_SECRET')
    if not secret:
        return False

    # Basic signature over raw body (can be extended to include timestamp/nonce if upstream supports it)
    sig_header = request.headers.get('X-Signature') or request.META.get('HTTP_X_SIGNATURE')
    if not sig_header or not sig_header.startswith('sha256='):
        return False
    sent_sig = sig_header.split('=', 1)[1].strip()
    body = request.body or b''
    calc_sig = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    try:
        if not hmac.compare_digest(calc_sig, sent_sig):
            return False
    except Exception:
        return False

    # Replay protection: timestamp + nonce
    ts_str = request.headers.get('X-Timestamp') or request.META.get('HTTP_X_TIMESTAMP')
    nonce = request.headers.get('X-Nonce') or request.META.get('HTTP_X_NONCE')
    ts = _parse_timestamp(ts_str)
    if not ts or not nonce:
        return False
    now = dj_timezone.now()
    # Ensure both datetimes are timezone-aware for comparison
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    # Max allowed skew: 300 seconds
    skew = abs((now - ts).total_seconds())
    if skew > 300:
        return False
    # Reject if nonce already seen
    if WebhookReplay.objects.filter(pk=nonce).exists():
        return False
    # Store the nonce (cleanup policy handled via DB TTL/cron if needed)
    try:
        WebhookReplay.objects.create(nonce=nonce)
    except Exception:
        # In case of race condition creating the same nonce, treat as replay
        return False
    return True
