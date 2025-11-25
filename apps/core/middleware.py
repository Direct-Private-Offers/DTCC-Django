import uuid
from typing import Optional
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.db import transaction
from .models import ApiSession


class RequestIDMiddleware(MiddlewareMixin):
    """Attach a unique request id to each response via X-Request-ID header."""

    def process_request(self, request):
        request.request_id = str(uuid.uuid4())

    def process_response(self, request, response):
        req_id = getattr(request, 'request_id', None) or str(uuid.uuid4())
        response["X-Request-ID"] = req_id
        return response


class SessionActivityMiddleware(MiddlewareMixin):
    """
    Very lightweight session tracking. For authenticated requests, attempts to
    extract JWT `jti` and subject, and upserts an ApiSession row, incrementing
    request_count and updating last_seen, ip, and user_agent.
    """

    def _extract_jwt_claims(self, request) -> Optional[dict]:
        # DRF SimpleJWT sets request.user and request.auth
        auth = getattr(request, 'auth', None)
        if isinstance(auth, dict):
            return auth
        payload = getattr(auth, 'payload', None)
        if isinstance(payload, dict):
            return payload
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        claims = self._extract_jwt_claims(request) or {}
        jti = claims.get('jti') or f'user-{user.id}'
        subject = str(claims.get('sub') or user.id)

        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT')

        # Upsert-like behavior for the session record
        now = timezone.now()
        with transaction.atomic():
            sess, created = ApiSession.objects.select_for_update().get_or_create(
                jti=jti,
                defaults={
                    'subject': subject,
                    'ip': ip,
                    'user_agent': ua,
                    'request_count': 0,
                },
            )
            # Update on each request
            sess.subject = subject
            if ip:
                sess.ip = ip
            if ua:
                sess.user_agent = ua
            sess.request_count = (sess.request_count or 0) + 1
            sess.last_seen = now
            sess.save(update_fields=['subject', 'ip', 'user_agent', 'request_count', 'last_seen'])
        return None
