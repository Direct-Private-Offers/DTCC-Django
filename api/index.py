import os
import sys
import json

# Ensure the Django app root is importable when running on Vercel
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()

# Vercel Python runtime can invoke a WSGI callable named `app` or `handler`.
# We expose both for compatibility without external adapters.
handler = app
