"""
Dev-Test settings for Adakings Backend API
Production-like configuration with test/placeholder values for safe testing
"""

from .base import *
import os
from django.core.management.utils import get_random_secret_key

# SECURITY WARNING: Test secret key for dev-test environment
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-dev-test-secret-key-for-testing-only')

# SECURITY WARNING: Debug mode off to simulate production
DEBUG = False

# Dev-test hosts
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,test.adakings.local,dev-test.adakings.local').split(',')

# Database - PostgreSQL for dev-test (with test database)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'adakings_dev_test'),
        'USER': os.environ.get('DB_USER', 'test_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'test_password_123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            # No SSL requirement for test environment
        },
    }
}

# Static files configuration for dev-test
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration for dev-test
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Security settings (relaxed for testing)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 0  # Disabled for dev-test
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_SSL_REDIRECT = False  # Disabled for dev-test
SESSION_COOKIE_SECURE = False  # Disabled for dev-test
CSRF_COOKIE_SECURE = False  # Disabled for dev-test
X_FRAME_OPTIONS = 'DENY'

# CORS settings for dev-test
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://test.adakings.local').split(',')
CORS_ALLOW_CREDENTIALS = True

# Session settings for dev-test
SESSION_COOKIE_SAMESITE = 'Lax'  # More relaxed for testing
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000,http://test.adakings.local').split(',')

# Email settings for dev-test (test SMTP or console)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.mailtrap.io')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '2525'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'test_user')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'test_password')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'test@adakings.local')

# Paystack settings for dev-test (test keys only)
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY_LIVE', 'pk_test_placeholder_public_key_dev_test')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY_LIVE', 'sk_test_placeholder_secret_key_dev_test')

# Logging configuration for dev-test
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
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'dev-test.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Cache configuration for dev-test (Redis with test database)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session cache (use Redis for dev-test)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Performance optimizations
USE_TZ = True
USE_I18N = True
USE_L10N = True

# DRF Spectacular settings for dev-test (enable for testing)
SPECTACULAR_SETTINGS.update({
    'SERVE_INCLUDE_SCHEMA': True,  # Enable for dev-test
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,  # More detailed for testing
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
})

# Enable additional development features for testing
if os.environ.get('ENABLE_SWAGGER_UI', 'True').lower() == 'true':
    INSTALLED_APPS += ['drf_spectacular_sidecar']

if os.environ.get('ENABLE_DEBUG_TOOLBAR', 'False').lower() == 'true':
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# JWT settings for dev-test (more relaxed)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),  # Longer for testing
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Longer for testing
    'SIGNING_KEY': SECRET_KEY,
})

# Health check settings
HEALTH_CHECK_ENDPOINTS = [
    'health/',
    'api/health/',
]

# Performance settings (more relaxed for testing)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB for testing
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB for testing

# API rate limiting (more relaxed for testing)
RATELIMIT_ENABLE = os.environ.get('RATE_LIMIT_ENABLE', 'True').lower() == 'true'

print("🧪 Dev-Test environment loaded successfully!")
print(f"📍 Allowed hosts: {ALLOWED_HOSTS}")
print(f"🔒 SSL redirect: {SECURE_SSL_REDIRECT}")
print(f"💾 Database: PostgreSQL (Test)")
print(f"📧 Email backend: SMTP (Test)")
print("⚠️  WARNING: Using placeholder/test values - not for production!")
