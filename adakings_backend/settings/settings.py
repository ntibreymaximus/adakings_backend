"""
Unified Django Settings for Adakings Backend API
Consolidates all environment-specific configurations into a single file
"""

from pathlib import Path
import os
import sys
import logging
from datetime import timedelta

# Load environment variables from .env file
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment variables from: {env_path}")
else:
    logging.warning(
        "No .env file found. Environment variables must be set manually. "
        "See .env.example for required variables."
    )

# SECURITY WARNING: Secret key
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-dev-secret-key-change-in-production')

# SECURITY WARNING: Debug mode
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'on', 'yes')

# Allowed hosts
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,*.localhost,0.0.0.0').split(',')

# Allow all hosts in development for network access
if DEBUG:
    ALLOWED_HOSTS += ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom apps
    'apps.users',
    'apps.menu',
    'apps.orders',
    'apps.payments',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'corsheaders',
    'channels',
]

# Enable development tools if available and in debug mode
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE_DEBUG = ['debug_toolbar.middleware.DebugToolbarMiddleware']
    except ImportError:
        MIDDLEWARE_DEBUG = []
    
    try:
        import drf_spectacular_sidecar
        INSTALLED_APPS += ['drf_spectacular_sidecar']
    except ImportError:
        pass
else:
    MIDDLEWARE_DEBUG = []

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'apps.orders.middleware.BrokenPipeMiddleware',  # Handle broken pipe errors
    'apps.orders.middleware.WebSocketConnectionMiddleware',  # Handle WebSocket connections
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
] + MIDDLEWARE_DEBUG

ROOT_URLCONF = 'adakings_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'adakings_backend.wsgi.application'
ASGI_APPLICATION = 'adakings_backend.asgi.application'

# Database configuration
database_engine = os.environ.get('DATABASE_ENGINE', 'sqlite3').lower()

if database_engine == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'adakings_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
# Default to SQLite for development with optimizations
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.environ.get('DATABASE_NAME', 'db.sqlite3'),
            'OPTIONS': {
                'timeout': 5,  # Reduced timeout for faster responses
                'check_same_thread': False,
                # SQLite optimizations for speed
                'init_command': (
                    "PRAGMA foreign_keys=ON;"
                    "PRAGMA journal_mode=WAL;"
                    "PRAGMA synchronous=NORMAL;"
                    "PRAGMA cache_size=10000;"
                    "PRAGMA temp_store=MEMORY;"
                    "PRAGMA mmap_size=134217728;"
                ),
            },
            'CONN_MAX_AGE': 300,  # Keep connections alive for 5 minutes for better performance
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings
SECURE_BROWSER_XSS_FILTER = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = not DEBUG
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0' if DEBUG else '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False' if DEBUG else 'True').lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'False' if DEBUG else 'True').lower() == 'true'
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = 'SAMEORIGIN' if DEBUG else 'DENY'

# CORS settings
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    CORS_ALLOW_CREDENTIALS = False

# Session settings
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '1025'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@adakings.local')

# Paystack settings
PAYSTACK_BASE_URL = 'https://api.paystack.co'
PAYMENT_CURRENCY = 'GHS'  # Ghana Cedis
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY_TEST', 'pk_test_placeholder_public_key')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY_TEST', 'sk_test_placeholder_secret_key')

# Function to check if Paystack is properly configured
def is_paystack_configured():
    """Check if Paystack API keys are properly configured."""
    return (PAYSTACK_PUBLIC_KEY and PAYSTACK_SECRET_KEY and 
            not PAYSTACK_PUBLIC_KEY.endswith('_placeholder_public_key') and
            not PAYSTACK_SECRET_KEY.endswith('_placeholder_secret_key'))

# Cache configuration
redis_url = os.environ.get('REDIS_URL')
if redis_url and not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
        }
    }
else:
    # Use dummy cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Channels layer configuration
redis_url = os.environ.get('REDIS_URL')
if redis_url and not DEBUG:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [redis_url],
                'capacity': 1500,  # Default 100
                'expiry': 60,      # Default 60 seconds
                'prefix': 'adakings:',
                'symmetric_encryption_keys': [SECRET_KEY],
            },
        },
    }
else:
    # Use in-memory channel layer for development
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
            'CONFIG': {
                'capacity': 500,   # Reduced for development
                'expiry': 30,      # Shorter expiry for development
            },
        },
    }

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,  # Increased page size for fewer API calls and instant loading
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else 'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '600/hour',  # Even higher rate for instant responsiveness
        'user': '2000/hour'  # Much higher rate for authenticated users
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'UNAUTHENTICATED_USER': 'django.contrib.auth.models.AnonymousUser',
    'UNAUTHENTICATED_TOKEN': None,
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Adakings Backend API',
    'DESCRIPTION': 'RESTful API for Adakings Restaurant Management System',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': DEBUG,
    'ENUM_NAME_OVERRIDES': {
        'OrderStatusEnum': 'apps.orders.models.Order.STATUS_CHOICES',
        'PaymentStatusEnum': 'apps.payments.models.Payment.PAYMENT_STATUS_CHOICES',
        'PaymentTransactionStatusEnum': 'apps.payments.models.PaymentTransaction.TRANSACTION_STATUS_CHOICES',
    },
    'SCHEMA_PATH_PREFIX': '/api/',
    'DEFAULT_GENERATOR_CLASS': 'drf_spectacular.generators.SchemaGenerator',
}

if DEBUG:
    SPECTACULAR_SETTINGS.update({
        'SWAGGER_UI_SETTINGS': {
            'deepLinking': True,
            'persistAuthorization': True,
            'displayOperationId': True,
        },
        'COMPONENT_SPLIT_REQUEST': True,
        'SORT_OPERATIONS': False,
    })

# JWT Settings
ACCESS_TOKEN_LIFETIME = timedelta(hours=8 if DEBUG else 1)
REFRESH_TOKEN_LIFETIME = timedelta(days=30 if DEBUG else 7)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': ACCESS_TOKEN_LIFETIME,
    'REFRESH_TOKEN_LIFETIME': REFRESH_TOKEN_LIFETIME,
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'cache-control',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# WebSocket and Connection Settings - Optimized for faster responsiveness
WEBSOCKET_TIMEOUT = int(os.environ.get('WEBSOCKET_TIMEOUT', '120'))  # 2 minutes for faster resource management
WEBSOCKET_HEARTBEAT_INTERVAL = int(os.environ.get('WEBSOCKET_HEARTBEAT_INTERVAL', '15'))  # 15 seconds for faster detection
CONNECTION_MAX_AGE = int(os.environ.get('CONNECTION_MAX_AGE', '120'))  # 2 minutes for faster cleanup
WEBSOCKET_CLOSE_TIMEOUT = int(os.environ.get('WEBSOCKET_CLOSE_TIMEOUT', '5'))  # 5 seconds for graceful close
WEBSOCKET_PING_INTERVAL = int(os.environ.get('WEBSOCKET_PING_INTERVAL', '10'))  # 10 seconds server-side ping
WEBSOCKET_PING_TIMEOUT = int(os.environ.get('WEBSOCKET_PING_TIMEOUT', '5'))  # 5 seconds pong timeout

# Add connection settings to database
for db_config in DATABASES.values():
    if 'postgresql' in db_config.get('ENGINE', ''):
        db_config['CONN_MAX_AGE'] = CONNECTION_MAX_AGE
        db_config['OPTIONS'] = db_config.get('OPTIONS', {})
        db_config['OPTIONS']['connect_timeout'] = 10
        db_config['OPTIONS']['tcp_keepalives_idle'] = 600
        db_config['OPTIONS']['tcp_keepalives_interval'] = 30
        db_config['OPTIONS']['tcp_keepalives_count'] = 3

# Custom logging filter to suppress broken pipe messages
class BrokenPipeFilter(logging.Filter):
    """Filter to suppress broken pipe and similar connection error messages."""
    
    def filter(self, record):
        # Only suppress broken pipe messages in production (not in DEBUG mode)
        if DEBUG:
            return True  # Show all messages in debug mode
            
        # Suppress broken pipe messages in production only
        message = record.getMessage().lower()
        suppressed_messages = [
            'broken pipe',
            'connection reset',
            'connection aborted',
            'client disconnected',
            'wsgi application',  # Some WSGI broken pipe messages
        ]
        
        for suppressed in suppressed_messages:
            if suppressed in message:
                return False
        
        return True

# Request logging filter to show HTTP request details
class RequestLoggingFilter(logging.Filter):
    """Filter to add request information to log records."""
    
    def filter(self, record):
        # Add request info if available
        import threading
        try:
            # Try to get current request from thread-local storage
            from django.utils.log import request_logger
            record.request_info = getattr(threading.current_thread(), 'request_info', '')
        except:
            record.request_info = ''
        return True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'broken_pipe_filter': {
            '()': BrokenPipeFilter,
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'websocket': {
            'format': 'WS {levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['broken_pipe_filter'],
        },
        'file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
            'filters': ['broken_pipe_filter'],
        },
        'websocket_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'websocket.log'),
            'formatter': 'websocket',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
        'filters': ['broken_pipe_filter'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
            'filters': ['broken_pipe_filter'],
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'WARNING',  # Reduce server logging level
            'propagate': False,
            'filters': ['broken_pipe_filter'],
        },
        'apps': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.orders.consumers': {
            'handlers': ['console', 'websocket_file'] if not DEBUG else ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'daphne': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
            'filters': ['broken_pipe_filter'],
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Performance settings - Optimized for faster responses
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', '5242880'))  # 5MB for faster processing
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', '5242880'))  # 5MB for faster processing

# Database connection optimization
DATABASE_CONN_MAX_AGE = 60  # Keep connections alive for better performance
DATABASE_QUERY_TIMEOUT = 10  # Faster query timeout

# Auto-reloader optimization for development
if DEBUG:
    # Reduce file watching intensity to prevent high CPU usage
    USE_TZ = True
    
    # Optimize auto-reload settings for stability
    import django.utils.autoreload
    
    # Disable inotify on Windows to prevent file watching issues
    django.utils.autoreload.USE_INOTIFY = False
    
    # Set reasonable polling interval (default is 1 second, increase to 2 seconds)
    os.environ.setdefault('DJANGO_AUTORELOAD_POLL_INTERVAL', '2')
    
    # Prevent excessive bytecode generation
    os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
    
    # Disable auto-reload if environment variable is set
    if os.environ.get('DISABLE_AUTO_RELOAD', 'False').lower() == 'true':
        django.utils.autoreload.USE_INOTIFY = False
        
    # Limit the number of file watchers and exclude certain directories
    import sys
    if hasattr(sys, '_getframe'):
        # Add directories to ignore for file watching
        AUTORELOAD_IGNORE_PATHS = [
            os.path.join(BASE_DIR, '__pycache__'),
            os.path.join(BASE_DIR, '*.pyc'),
            os.path.join(BASE_DIR, 'logs'),
            os.path.join(BASE_DIR, '.git'),
            os.path.join(BASE_DIR, 'node_modules'),
            os.path.join(BASE_DIR, 'static'),
            os.path.join(BASE_DIR, 'media'),
        ]

# API rate limiting
RATELIMIT_ENABLE = os.environ.get('RATE_LIMIT_ENABLE', 'False').lower() == 'true'

# Debug toolbar configuration
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Print configuration info (only once)
if not os.environ.get('DJANGO_SETTINGS_LOADED'):
    os.environ['DJANGO_SETTINGS_LOADED'] = 'unified'
    print("Unified Django settings loaded successfully!")
    print(f"Debug mode: {DEBUG}")
    print(f"Allowed hosts: {ALLOWED_HOSTS}")
    print(f"Database: {'PostgreSQL' if database_engine == 'postgresql' else 'SQLite'}")
    print(f"Email backend: {EMAIL_BACKEND}")
    print(f"Paystack configured: {is_paystack_configured()}")
    print("Ready for development and production!")
