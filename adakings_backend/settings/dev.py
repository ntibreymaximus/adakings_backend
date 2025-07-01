"""
Dev settings for Adakings Backend API
Production-like configuration but with development-safe values
"""

from .base import *
import os
from django.core.management.utils import get_random_secret_key

# SECURITY WARNING: Dev secret key (not for production)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-dev-secret-key-for-development-only')

# SECURITY WARNING: Debug mode off for production-like testing
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

# Dev hosts
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,dev.adakings.local').split(',')

# Database - PostgreSQL for production-like testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'adakings_dev'),
        'USER': os.environ.get('DB_USER', 'dev_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'dev_password_123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'prefer',  # More relaxed than production
        },
    }
}

# Static files configuration for dev
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration for dev
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Security settings (production-like but relaxed for development)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 0  # Disabled for dev
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
X_FRAME_OPTIONS = 'SAMEORIGIN'  # More relaxed than production

# CORS settings for dev
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://dev.adakings.local').split(',')
CORS_ALLOW_CREDENTIALS = True

# Session settings for dev
SESSION_COOKIE_SAMESITE = 'Lax'  # More relaxed than production
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000,http://dev.adakings.local').split(',')

# Email settings for dev (test SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.mailtrap.io')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '2525'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'dev_user')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'dev_password')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'dev@adakings.local')

# Paystack settings for dev (test keys only)
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY_LIVE', 'pk_test_dev_public_key_placeholder')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY_LIVE', 'sk_test_dev_secret_key_placeholder')

# Warn if using placeholder keys
if 'placeholder' in PAYSTACK_PUBLIC_KEY or 'placeholder' in PAYSTACK_SECRET_KEY:
    print("⚠️  Warning: Using placeholder Paystack keys in dev environment")

# Logging configuration for dev
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
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'dev.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Cache configuration for dev (Redis for production-like testing)
redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')
if redis_url and redis_url != 'redis://127.0.0.1:6379/1':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Fallback to dummy cache if Redis not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Session cache (use database for dev if Redis not available)
if redis_url and redis_url != 'redis://127.0.0.1:6379/1':
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Performance optimizations
USE_TZ = True
USE_I18N = True
USE_L10N = True

# DRF Spectacular settings for dev (enable documentation)
SPECTACULAR_SETTINGS.update({
    'SERVE_INCLUDE_SCHEMA': os.environ.get('ENABLE_SWAGGER_UI', 'True').lower() == 'true',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
})

# JWT settings for dev (production-like but slightly more convenient)
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Slightly longer than production
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Longer for development convenience
    'SIGNING_KEY': SECRET_KEY,
})

# Performance settings (production-like)
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 5242880))  # 5MB default
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 5242880))  # 5MB default

# API rate limiting (enabled but relaxed for dev)
RATELIMIT_ENABLE = os.environ.get('RATE_LIMIT_ENABLE', 'True').lower() == 'true'

# Enable development tools if requested
if os.environ.get('ENABLE_DEBUG_TOOLBAR', 'False').lower() == 'true':
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
    except ImportError:
        print("⚠️  Warning: debug_toolbar requested but not installed")

# Only print environment info once
if not os.environ.get('DJANGO_SETTINGS_LOADED'):
    os.environ['DJANGO_SETTINGS_LOADED'] = 'dev'
    print("🔧 Dev environment loaded successfully!")
    print(f"📍 Allowed hosts: {ALLOWED_HOSTS}")
    print(f"🔒 Debug mode: {DEBUG}")
    print(f"🔒 SSL redirect: {SECURE_SSL_REDIRECT}")
    print(f"💾 Database: PostgreSQL (Dev)")
    print(f"📧 Email backend: SMTP (Test)")
    print("🚀 Ready for production-like development!")
