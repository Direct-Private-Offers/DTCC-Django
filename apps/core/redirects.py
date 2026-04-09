import logging
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseRedirect

from .models import RedirectEvent

logger = logging.getLogger(__name__)


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip('/')


def _normalize_path(path: str) -> str:
    if not path.startswith('/'):
        return f'/{path}'
    return path


def _coerce_query_params(get_params):
    data = {}
    for key, values in get_params.lists():
        if len(values) == 1:
            data[key] = values[0]
        else:
            data[key] = values
    return data


def _get_param(query_params: dict, key: str):
    value = query_params.get(key)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def redirect_cta(request, route: str):
    routes = getattr(settings, 'CTA_REDIRECT_ROUTES', {})
    if route not in routes:
        return HttpResponseNotFound("Unknown redirect route")

    base_url = _normalize_base_url(getattr(settings, 'PAYBITO_BASE_URL', ''))
    if not base_url:
        return HttpResponseNotFound("Redirect base URL not configured")

    target_path = _normalize_path(routes[route])
    target_url = f"{base_url}{target_path}"

    query_params = _coerce_query_params(request.GET)
    if query_params:
        target_url = f"{target_url}?{urlencode(query_params, doseq=True)}"

    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    referrer = request.META.get('HTTP_REFERER')
    request_id = getattr(request, 'request_id', None)

    try:
        RedirectEvent.objects.create(
            route=route,
            target_url=target_url,
            query_params=query_params or None,
            utm_source=_get_param(query_params, 'utm_source'),
            utm_medium=_get_param(query_params, 'utm_medium'),
            utm_campaign=_get_param(query_params, 'utm_campaign'),
            utm_term=_get_param(query_params, 'utm_term'),
            utm_content=_get_param(query_params, 'utm_content'),
            gclid=_get_param(query_params, 'gclid'),
            fbclid=_get_param(query_params, 'fbclid'),
            msclkid=_get_param(query_params, 'msclkid'),
            referrer=referrer,
            ip=ip,
            user_agent=user_agent,
            request_id=request_id,
        )
    except Exception as exc:  # pragma: no cover - tracking should never block redirect
        logger.warning("Redirect tracking failed for route %s: %s", route, exc)

    return HttpResponseRedirect(target_url)
