import os
import sys
import json

# Ensure the Django app (backend/) is importable when running on Vercel
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()

# Vercel Python functions typically use an adapter like vercel-wsgi.
# To avoid a hard runtime dependency that may not be available in your environment,
# we conditionally import it. If absent, we expose a minimal fallback handler that
# returns a diagnostic response. This keeps installations working without the
# vercel-wsgi package while allowing local WSGI (gunicorn/runserver) to function.
try:
    from vercel_wsgi import handle  # type: ignore

    def handler(event, context):
        return handle(event, context, app)
except Exception:  # pragma: no cover
    def handler(event, context):
        # Fallback: simple diagnostic. For full serverless support on Vercel,
        # add the 'vercel-wsgi' dependency or run Django via a container.
        return {
            "statusCode": 501,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "error": "vercel-wsgi not installed; use standard WSGI (gunicorn) or add vercel-wsgi to enable Vercel serverless.",
                "timestamp": ""
            }),
        }
