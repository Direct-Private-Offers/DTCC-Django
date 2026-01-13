import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
ALLOWED_HOSTS = os. getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'django. contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django. contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    # 'apps.core',
    'apps.euroclear',
    'apps.issuance',
    'apps. derivatives',
    'apps.settlement',
    'apps.corporate_actions',
    'apps.clearstream',
    'apps.webhooks',
    'apps. dex',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 'django.contrib.sessions. middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django. middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth. middleware.AuthenticationMiddleware',
    # 'django.contrib.messages. middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.RequestIDMiddleware',
    # 'apps.core.middleware. SessionActivityMiddleware',
]

ROOT_URLCONF = 'config. urls'

TEMPLATES = [
    {
        'BACKEND':  'django.template.backends. django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                # 'django.contrib.auth. context_processors.auth',
                # 'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi. application'
ASGI_APPLICATION = 'config.asgi.application'

# Database configuration - PostgreSQL required
# Set DATABASE_URL environment variable, e.g.: 
# postgres://user:password@localhost:5432/dbname
# or for PostgreSQL with SSL:
# postgres://user:password@host:5432/dbname?sslmode=require
DATABASE_URL = os.getenv('DATABASE_URL', None)

if DATABASE_URL:
    DATABASES = {
        'default':  dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

    # PostgreSQL-specific optimizations
    if DATABASES['default']['ENGINE'] == 'django.db. backends.postgresql':
        # Merge with existing options if any
        existing_options = DATABASES['default'].get('OPTIONS', {})
        existing_options.update({
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 seconds
        })
        DATABASES['default']['OPTIONS'] = existing_options
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db. backends.dummy',
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling. UserRateThrottle',
        'rest_framework.throttling. AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': os.getenv('RATE_LIMIT_USER', '100/min'),
        'anon': os.getenv('RATE_LIMIT_ANON', '20/min'),
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'DTCC STO Backend API',
    'DESCRIPTION': 'Django/DRF API for DTCC-compliant STO with Euroclear/Clearstream integrations',
    'VERSION':  '1.0.0',
}

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Security & Headers
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'false' if DEBUG else 'true').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# CORS - Configured for localhost development
CORS_ALLOW_CREDENTIALS = True
cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
if cors_origins:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins.split(',') if o.strip()]
else:
    # Default localhost origins for development
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

# Blockchain Configuration
QUICKNODE_URL = os.getenv('QUICKNODE_URL', '')
BLOCKCHAIN_RPC_URL = os.getenv('BLOCKCHAIN_RPC_URL', QUICKNODE_URL)
ISSUANCE_CONTRACT_ADDRESS = os.getenv('ISSUANCE_CONTRACT_ADDRESS', '')
ISSUANCE_CONTRACT_ABI = os.getenv('ISSUANCE_CONTRACT_ABI', '')
BLOCKCHAIN_NETWORK = os.getenv('BLOCKCHAIN_NETWORK', 'BSC')
START_BLOCK_NUMBER = int(os.getenv('START_BLOCK_NUMBER', '0'))