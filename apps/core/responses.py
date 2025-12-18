from django.utils import timezone
from rest_framework.response import Response


def envelope(success: bool, data=None, error=None, status: int = 200):
    body = {
        'success': success,
        'timestamp': timezone.now().isoformat() + 'Z',
    }
    if success and data is not None:
        body['data'] = data
    if not success and error is not None:
        body['error'] = error
    return Response(body, status=status)


def ok(data=None, status: int = 200):
    return envelope(True, data=data, status=status)


def bad_request(error: str, status: int = 400):
    return envelope(False, error=error, status=status)


def not_found(error: str = 'Not found'):
    return envelope(False, error=error, status=404)


def unauthorized(error: str = 'Unauthorized'):
    return envelope(False, error=error, status=401)
