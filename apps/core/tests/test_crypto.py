"""
Tests for cryptographic utilities.
"""
import pytest
import hmac
import hashlib
from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta
from apps.core.crypto import verify_hmac, _parse_timestamp
from apps.core.models import WebhookReplay
import os


class TestHMACVerification:
    """Test HMAC signature verification."""
    
    @pytest.fixture
    def secret(self):
        """Set webhook secret."""
        os.environ['WEBHOOK_SECRET'] = 'test-secret-key'
        yield 'test-secret-key'
        if 'WEBHOOK_SECRET' in os.environ:
            del os.environ['WEBHOOK_SECRET']
    
    @pytest.fixture
    def request_factory(self):
        """Request factory for creating test requests."""
        return RequestFactory()
    
    def test_verify_hmac_valid_signature(self, secret, request_factory):
        """Test valid HMAC signature verification."""
        body = b'{"event": "test", "data": {}}'
        signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        request = request_factory.post(
            '/webhook',
            data=body,
            content_type='application/json',
            HTTP_X_SIGNATURE=f'sha256={signature}',
            HTTP_X_TIMESTAMP=str(int(timezone.now().timestamp())),
            HTTP_X_NONCE='test-nonce-123'
        )
        request.body = body
        
        # Clear any existing nonce
        WebhookReplay.objects.filter(nonce='test-nonce-123').delete()
        
        assert verify_hmac(request) is True
    
    def test_verify_hmac_invalid_signature(self, secret, request_factory):
        """Test invalid HMAC signature."""
        body = b'{"event": "test"}'
        request = request_factory.post(
            '/webhook',
            data=body,
            content_type='application/json',
            HTTP_X_SIGNATURE='sha256=invalid-signature',
            HTTP_X_TIMESTAMP=str(int(timezone.now().timestamp())),
            HTTP_X_NONCE='test-nonce-456'
        )
        request.body = body
        
        assert verify_hmac(request) is False
    
    def test_verify_hmac_missing_headers(self, secret, request_factory):
        """Test missing required headers."""
        body = b'{"event": "test"}'
        request = request_factory.post('/webhook', data=body)
        request.body = body
        
        assert verify_hmac(request) is False
    
    def test_verify_hmac_expired_timestamp(self, secret, request_factory):
        """Test expired timestamp."""
        body = b'{"event": "test"}'
        expired_timestamp = int((timezone.now() - timedelta(seconds=400)).timestamp())
        signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        request = request_factory.post(
            '/webhook',
            data=body,
            content_type='application/json',
            HTTP_X_SIGNATURE=f'sha256={signature}',
            HTTP_X_TIMESTAMP=str(expired_timestamp),
            HTTP_X_NONCE='test-nonce-789'
        )
        request.body = body
        
        assert verify_hmac(request) is False
    
    def test_verify_hmac_replay_attack(self, secret, request_factory):
        """Test nonce replay protection."""
        body = b'{"event": "test"}'
        signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        nonce = 'replay-nonce-123'
        timestamp = str(int(timezone.now().timestamp()))
        
        # First request should succeed
        request1 = request_factory.post(
            '/webhook',
            data=body,
            content_type='application/json',
            HTTP_X_SIGNATURE=f'sha256={signature}',
            HTTP_X_TIMESTAMP=timestamp,
            HTTP_X_NONCE=nonce
        )
        request1.body = body
        
        WebhookReplay.objects.filter(nonce=nonce).delete()
        assert verify_hmac(request1) is True
        
        # Second request with same nonce should fail
        request2 = request_factory.post(
            '/webhook',
            data=body,
            content_type='application/json',
            HTTP_X_SIGNATURE=f'sha256={signature}',
            HTTP_X_TIMESTAMP=timestamp,
            HTTP_X_NONCE=nonce
        )
        request2.body = body
        
        assert verify_hmac(request2) is False


class TestTimestampParsing:
    """Test timestamp parsing utilities."""
    
    def test_parse_epoch_timestamp(self):
        """Test parsing epoch timestamp."""
        epoch = int(timezone.now().timestamp())
        result = _parse_timestamp(str(epoch))
        assert result is not None
        assert isinstance(result, timezone.datetime)
    
    def test_parse_iso_timestamp(self):
        """Test parsing ISO 8601 timestamp."""
        iso_str = timezone.now().isoformat()
        result = _parse_timestamp(iso_str)
        assert result is not None
    
    def test_parse_invalid_timestamp(self):
        """Test parsing invalid timestamp."""
        result = _parse_timestamp('invalid-timestamp')
        assert result is None
    
    def test_parse_empty_timestamp(self):
        """Test parsing empty timestamp."""
        result = _parse_timestamp('')
        assert result is None
        result = _parse_timestamp(None)
        assert result is None

