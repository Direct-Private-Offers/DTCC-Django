import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY must be set in production - fail if not provided
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.getenv('ENVIRONMENT') == 'production' or not os.getenv('ENVIRONMENT'):
        raise ValueError("DJANGO_SECRET_KEY environment variable must be set in production")
    SECRET_KEY = 'dev-secret-key-change-me-in-production'

# DEBUG defaults to False for security
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
# Fail-safe: if ENVIRONMENT is production, force DEBUG=False
if os.getenv('ENVIRONMENT') == 'production':
    DEBUG = False
# Parse ALLOWED_HOSTS from environment variable
allowed_hosts_env = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]

# Automatically add Vercel deployment domains when running on Vercel
if os.getenv('VERCEL'):
    # Add the specific deployment URL (e.g., abc123-project.vercel.app)
    vercel_url = os.getenv('VERCEL_URL')
    if vercel_url and vercel_url not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(vercel_url)
    
    # Add wildcard for all Vercel preview deployments
    if '.vercel.app' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('.vercel.app')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'apps.core',
    'apps.euroclear',
    'apps.issuance',
    'apps.derivatives',
    'apps.settlement',
    'apps.corporate_actions',
    'apps.clearstream',
    'apps.webhooks',
    'apps.dex',
    'apps.api',
    'apps.compliance',
    'apps.notifications',
    'apps.reports',
    'apps.storage',
    'apps.payments',  # Bill Bitts / NEO Bank payment integration
    'apps.issuers',  # Issuer onboarding (BD integration)
    'apps.xetra',
    'apps.receipts',
    'apps.neo_bank',
    'apps.fx_market',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.RequestIDMiddleware',
    'apps.core.middleware.SessionActivityMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database configuration - PostgreSQL for production, SQLite for development
# Set DATABASE_URL environment variable, e.g.:
# postgres://user:password@localhost:5432/dbname
# or for PostgreSQL with SSL:
# postgres://user:password@host:5432/dbname?sslmode=require
# For SQLite: sqlite:///./db.sqlite3
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Default to SQLite for development
    DATABASE_URL = 'sqlite:///./db.sqlite3'
    if not DEBUG:
        raise ValueError(
            "DATABASE_URL environment variable is required in production. "
            "Set it to a PostgreSQL connection string, e.g.: "
            "postgres://user:password@localhost:5432/dbname"
        )

DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# PostgreSQL-specific optimizations
if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    # Merge with existing options if any
    existing_options = DATABASES['default'].get('OPTIONS', {})
    existing_options.update({
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000',  # 30 seconds
    })
    DATABASES['default']['OPTIONS'] = existing_options
    # Connection pooling is already set via conn_max_age above

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator' },
]

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
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': os.getenv('RATE_LIMIT_USER', '100/min'),
        'anon': os.getenv('RATE_LIMIT_ANON', '20/min'),
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'DTCC STO Backend API',
    'DESCRIPTION': 'Django/DRF API for DTCC-compliant STO with Euroclear/Clearstream integrations',
    'VERSION': '1.0.0',
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
# Production contract addresses (from deployment-proxy-addresses.json)
STO_CONTRACT_ADDRESS = os.getenv('STO_CONTRACT_ADDRESS', ISSUANCE_CONTRACT_ADDRESS)
DERIVATIVES_REPORTER_CONTRACT_ADDRESS = os.getenv('DERIVATIVES_REPORTER_CONTRACT_ADDRESS', '')
EUROCLEAR_BRIDGE_CONTRACT_ADDRESS = os.getenv('EUROCLEAR_BRIDGE_CONTRACT_ADDRESS', '')
ISSUANCE_CONTRACT_ABI = os.getenv('ISSUANCE_CONTRACT_ABI', '')
BLOCKCHAIN_NETWORK = os.getenv('BLOCKCHAIN_NETWORK', 'ARBITRUM_NOVA')  # ARBITRUM_NOVA, BSC, Ethereum, Polygon, etc.
START_BLOCK_NUMBER = int(os.getenv('START_BLOCK_NUMBER', '0'))

# Validate production contract addresses in production
if os.getenv('ENVIRONMENT') == 'production':
    if not STO_CONTRACT_ADDRESS:
        raise ValueError("STO_CONTRACT_ADDRESS must be set in production")
    if not BLOCKCHAIN_RPC_URL:
        raise ValueError("BLOCKCHAIN_RPC_URL or QUICKNODE_URL must be set in production")

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose' if DEBUG else 'json',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'dtcc.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.dex': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.issuance': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'dtcc',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# If Redis is not available, fallback to local memory cache
if not os.getenv('REDIS_URL'):
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dtcc-cache',
    }

# File Storage Configuration
FILE_STORAGE_ROOT = os.path.join(BASE_DIR, 'storage', 'files')
os.makedirs(FILE_STORAGE_ROOT, exist_ok=True)

# IPFS Configuration (optional)
IPFS_ENABLED = os.getenv('IPFS_ENABLED', 'false').lower() == 'true'
IPFS_GATEWAY_URL = os.getenv('IPFS_GATEWAY_URL', 'https://ipfs.io/ipfs/')
IPFS_API_URL = os.getenv('IPFS_API_URL', 'http://localhost:5001')

# API Versioning
REST_FRAMEWORK['DEFAULT_VERSIONING_CLASS'] = 'apps.core.versioning.CustomURLPathVersioning'
REST_FRAMEWORK['ALLOWED_VERSIONS'] = ['v1', 'v2']
REST_FRAMEWORK['DEFAULT_VERSION'] = 'v1'

# Email Configuration - SendGrid
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', os.getenv('DEFAULT_FROM_EMAIL', 'noreply@dtcc-sto.com'))
SENDGRID_FROM_NAME = os.getenv('SENDGRID_FROM_NAME', 'DTCC STO Backend')

# Django Email Backend
# Use SendGrid backend if API key is provided, otherwise fallback to console for development
if SENDGRID_API_KEY:
    EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
    SENDGRID_SANDBOX_MODE_IN_DEBUG = DEBUG  # Use sandbox mode in debug
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Fallback to console

DEFAULT_FROM_EMAIL = SENDGRID_FROM_EMAIL

# Bill Bitts / NEO Bank Payment Integration
BILLBITTS_API_URL = os.getenv('BILLBITTS_API_URL', 'https://api.billbitcoins.com')
BILLBITTS_API_KEY = os.getenv('BILLBITTS_API_KEY', '')
BILLBITTS_PRIVATE_KEY_PATH = os.getenv('BILLBITTS_PRIVATE_KEY_PATH', os.path.join(BASE_DIR, 'keys', 'billbitts_private.pem'))

# Omnisend Marketing Automation
OMNISEND_API_KEY = os.getenv('OMNISEND_API_KEY', '')

# CSD Credential Validation (warnings in production, not errors to allow development)
if os.getenv('ENVIRONMENT') == 'production':
    import logging
    logger = logging.getLogger(__name__)
    if not os.getenv('EUROCLEAR_API_KEY') or os.getenv('EUROCLEAR_API_BASE', '').endswith('.example'):
        logger.warning("Euroclear production credentials not configured")
    if not os.getenv('CLEARSTREAM_PMI_KEY') or os.getenv('CLEARSTREAM_PMI_BASE', '').endswith('.example'):
        logger.warning("Clearstream production credentials not configured")
    if not os.getenv('XETRA_API_KEY') or os.getenv('XETRA_API_BASE', '').endswith('.example'):
        logger.warning("XETRA production credentials not configured")
