from functools import wraps
from django.utils import timezone
from datetime import timedelta
from .models import IdempotencyKey
from rest_framework.response import Response
import json
import logging

logger = logging.getLogger(__name__)


def idempotent(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        key = request.headers.get('Idempotency-Key') or request.META.get('HTTP_IDEMPOTENCY_KEY')
        if key:
            try:
                rec = IdempotencyKey.objects.filter(key=key, path=request.path).first()
                if rec and rec.expires_at > timezone.now():
                    return Response(rec.response)
            except Exception as e:
                logger.warning(f"Error checking idempotency key: {str(e)}")
        
        resp: Response = view_func(self, request, *args, **kwargs)
        
        if key and 200 <= resp.status_code < 300:
            try:
                # Ensure response data is JSON serializable
                response_data = resp.data
                if response_data is not None:
                    # Test serialization
                    json.dumps(response_data)
                
                IdempotencyKey.objects.update_or_create(
                    key=key, path=request.path,
                    defaults={
                        'method': request.method,
                        'response': response_data,
                        'expires_at': timezone.now() + timedelta(hours=24),
                    }
                )
            except (TypeError, ValueError) as e:
                logger.warning(f"Response data not JSON serializable for idempotency key {key}: {str(e)}")
            except Exception as e:
                logger.error(f"Error storing idempotency key: {str(e)}")
        
        return resp
    return _wrapped
