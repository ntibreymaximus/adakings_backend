"""
Development settings for Adakings Backend API
Local development environment with debugging enabled
"""

from .base import *
import os
from django.core.management.utils import get_random_secret_key

# SECURITY WARNING: Development secret key (not for production)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-dev-secret-key-change-in-production')

# SECURITY WARNING: Debug mode on for development
DEBUG = True

# Development hosts
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Database - SQLite for development (simple setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Alternative PostgreSQL configuration (comment out SQLite above and uncomment below if needed)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'adakings_dev'),
#         'USER': os.environ.get('DB_USER', 'postgres'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
#         'HOST': os.environ.get('DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }

# Static files configuration for development
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration for development
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Security settings (relaxed for development)
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
X_FRAME_OPTIONS = 'SAMEORIGIN'

# CORS settings for development (allow all for local dev)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Session settings for development
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')

# Email settings for development (console backend for easy testing)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Paystack settings for development (test keys)
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY_TEST', 'pk_test_placeholder_public_key_dev')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY_TEST', 'sk_test_placeholder_secret_key_dev')

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'development.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Cache configuration for development (dummy cache for simplicity)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Alternative Redis cache configuration (uncomment if Redis is available)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
#     }
# }

# Session cache (use database for development)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Performance optimizations
USE_TZ = True
USE_I18N = True
USE_L10N = True

# DRF Spectacular settings for development (enable documentation)
SPECTACULAR_SETTINGS.update({
    'SERVE_INCLUDE_SCHEMA': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
})

# Enable development tools (only if available)
try:
    import drf_spectacular_sidecar
    INSTALLED_APPS += ['drf_spectacular_sidecar']
except ImportError:
    pass

# Enable Django Debug Toolbar if available
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# JWT settings for development (longer tokens for convenience)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),  # Longer for development
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # Longer for development
    'SIGNING_KEY': SECRET_KEY,
})

# Performance settings (more generous for development)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# API rate limiting (disabled for development)
RATELIMIT_ENABLE = False

# Only print environment info once
if not os.environ.get('DJANGO_SETTINGS_LOADED'):
    os.environ['DJANGO_SETTINGS_LOADED'] = 'development'
    print("🔧 Development environment loaded successfully!")
    print(f"📍 Allowed hosts: {ALLOWED_HOSTS}")
    print(f"🔒 Debug mode: {DEBUG}")
    print(f"💾 Database: SQLite (Development)")
    print(f"📧 Email backend: Console")
    print("🚀 Ready for local development!")
