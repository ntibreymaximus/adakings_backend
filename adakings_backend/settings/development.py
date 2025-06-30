"""
Development settings for Adakings Backend API
"""

from .base import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$d)4m^^$c*tb+oahwhl-1gjl*qip_i&dk_bj4-_5wg1!6x=_vt'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development hosts
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (Uploaded files)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email settings for development (using console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True  # Only use this for development
CORS_ALLOW_CREDENTIALS = True  # Allow cookies for cross-origin requests

# Cookie settings for cross-origin requests during development
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # Must be True in production if SameSite='None'

CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000', 
    'http://127.0.0.1:3000', 
    'http://localhost:8000', 
    'http://127.0.0.1:8000'
]

# Paystack API configuration for development (test keys)
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')

# Log a warning if Paystack is not configured
if not is_paystack_configured():
    logging.warning(
        "Paystack API keys are not configured. Mobile money payments will not work. "
        "Please set PAYSTACK_PUBLIC_KEY and PAYSTACK_SECRET_KEY environment variables."
    )

# DRF Spectacular settings for development
SPECTACULAR_SETTINGS.update({
    'SERVE_INCLUDE_SCHEMA': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
})

# Development logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}

print("🔧 Development settings loaded")
print(f"📍 Debug mode: {DEBUG}")
print(f"💾 Database: SQLite")
print(f"🌐 CORS: Allow all origins (dev only)")
