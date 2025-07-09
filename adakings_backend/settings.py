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
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection and configuration
# Railway provides environment variables directly for dev and prod
# Local development uses .env file

# Detect if we're running on Railway
IS_RAILWAY = 'RAILWAY_ENVIRONMENT' in os.environ

# Get environment from Railway variables or default to local
if IS_RAILWAY:
    # Use Railway's DJANGO_ENVIRONMENT variable for dev/prod
    ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')
else:
    # Load .env file for local development
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    # Get environment from .env file or default to local
    ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'local')

# SECURITY WARNING: Secret key
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-dev-secret-key-change-in-production')

# SECURITY WARNING: Debug mode - default to False in production
# Only enable debug if explicitly set to True
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'on', 'yes')

# Allowed hosts
allowed_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]

# Add Railway-specific hosts automatically
if 'RAILWAY_ENVIRONMENT' in os.environ or 'PORT' in os.environ:
    # Add Railway's public domain if available
    railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    railway_private_domain = os.environ.get('RAILWAY_PRIVATE_DOMAIN')
    
    if railway_public_domain:
        ALLOWED_HOSTS.append(railway_public_domain)
    if railway_private_domain:
        ALLOWED_HOSTS.append(railway_private_domain)
    
    # Add Railway's health check domains and wildcards
    ALLOWED_HOSTS.extend([
        'healthcheck.railway.app',
        '.railway.app',
        '.railway.internal',
        '*.up.railway.app',
        '*.railway.app'
    ])
    
    # If still no specific hosts, allow all for Railway
    if not railway_public_domain and not railway_private_domain:
        ALLOWED_HOSTS.append('*')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Core app for management commands
    'adakings_backend',
    
    # Custom apps
    'apps.users',
    'apps.menu',
    'apps.orders',
    'apps.payments',
    'apps.websockets',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'corsheaders',
    'channels',
]

# Enable development tools if available and in debug mode
MIDDLEWARE_DEBUG = []
if DEBUG:
    # Django Debug Toolbar
    if os.environ.get('ENABLE_DEBUG_TOOLBAR', 'True').lower() == 'true':
        try:
            import debug_toolbar
            INSTALLED_APPS += ['debug_toolbar']
            MIDDLEWARE_DEBUG += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        except ImportError:
            pass
    
    # Django Extensions
    if os.environ.get('ENABLE_DJANGO_EXTENSIONS', 'True').lower() == 'true':
        try:
            import django_extensions
            INSTALLED_APPS += ['django_extensions']
        except ImportError:
            pass
    
    # DRF Spectacular Sidecar
    try:
        import drf_spectacular_sidecar
        INSTALLED_APPS += ['drf_spectacular_sidecar']
    except ImportError:
        pass

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'adakings_backend.middleware.EnvironmentTagMiddleware',
] + MIDDLEWARE_DEBUG

ROOT_URLCONF = 'adakings_backend.urls'

# Disable APPEND_SLASH to prevent any automatic redirects
APPEND_SLASH = False

# Railway-specific settings to handle load balancer
if IS_RAILWAY:
    # Trust Railway's load balancer headers
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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
                'adakings_backend.context_processors.environment_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'adakings_backend.wsgi.application'
ASGI_APPLICATION = 'adakings_backend.asgi.application'

# Database configuration based on environment
if IS_RAILWAY:
    # Railway environments (dev/prod) use PostgreSQL
    # Railway provides PGDATABASE, PGUSER, PGPASSWORD, PGHOST, PGPORT automatically
    db_name = os.environ.get('PGDATABASE') or os.environ.get('DB_NAME') or 'railway'
    db_user = os.environ.get('PGUSER') or os.environ.get('DB_USER') or 'postgres'
    db_password = os.environ.get('PGPASSWORD') or os.environ.get('DB_PASSWORD') or ''
    db_host = os.environ.get('PGHOST') or os.environ.get('DB_HOST') or 'localhost'
    db_port = os.environ.get('PGPORT') or os.environ.get('DB_PORT') or '5432'
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port,
            'CONN_MAX_AGE': 0,  # Disable connection pooling to prevent threading issues
            'OPTIONS': {
                'connect_timeout': 10,
            },
            'ATOMIC_REQUESTS': True,  # Wrap each request in a transaction
        }
    }
else:
    # Local development uses SQLite
    database_name = os.environ.get('DATABASE_NAME', 'db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / database_name,
            'OPTIONS': {
                'timeout': 20,
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

# WhiteNoise configuration for static files - use StaticFilesStorage to avoid manifest issues
if IS_RAILWAY:
    # Use basic WhiteNoise storage for production to avoid manifest.json issues
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
else:
    # Use manifest storage for development
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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
    cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    # Clean up origins - remove trailing slashes and empty strings
    CORS_ALLOWED_ORIGINS = [origin.strip().rstrip('/') for origin in cors_origins if origin.strip()]
    CORS_ALLOW_CREDENTIALS = False

# Session settings
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Trusted origins for CSRF
csrf_origins_env = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_env.split(',') if origin.strip()]

# Add Railway HTTPS domains automatically
if IS_RAILWAY:
    railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    railway_private_domain = os.environ.get('RAILWAY_PRIVATE_DOMAIN')
    
    if railway_public_domain:
        CSRF_TRUSTED_ORIGINS.append(f'https://{railway_public_domain}')
    if railway_private_domain:
        CSRF_TRUSTED_ORIGINS.append(f'https://{railway_private_domain}')

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '1025'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@adakings.local')

# Paystack settings (COMMENTED OUT - NOT PROPERLY INTEGRATED YET)
# PAYSTACK_BASE_URL = 'https://api.paystack.co'
# PAYMENT_CURRENCY = 'GHS'  # Ghana Cedis
# PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY_TEST', 'pk_test_placeholder_public_key')
# PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY_TEST', 'sk_test_placeholder_secret_key')

# Function to check if Paystack is properly configured (COMMENTED OUT)
# def is_paystack_configured():
#     """Check if Paystack API keys are properly configured."""
#     return (PAYSTACK_PUBLIC_KEY and PAYSTACK_SECRET_KEY and 
#             not PAYSTACK_PUBLIC_KEY.endswith('_placeholder_public_key') and
#             not PAYSTACK_SECRET_KEY.endswith('_placeholder_secret_key'))

# Temporary placeholder function
def is_paystack_configured():
    """Paystack is not configured yet."""
    return False

# Cache configuration
redis_url = os.environ.get('REDIS_URL')
if redis_url and not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
            'TIMEOUT': 300,  # 5 minutes default timeout
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                }
            }
        }
    }
else:
    # Use local memory cache for development (faster than dummy cache)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,  # 5 minutes
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }

# Session cache - use database backend with proper threading safety
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Channel layers configuration for WebSocket support
redis_url = os.environ.get('REDIS_URL')
if redis_url and not DEBUG:
    # Use Redis for production WebSocket channels
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [redis_url],
                'capacity': 1500,
                'expiry': 60,
            },
        },
    }
else:
    # Use in-memory channel layer for development
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
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
        'rest_framework.renderers.BrowsableAPIRenderer',
    ] if DEBUG else [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/minute' if DEBUG else '600/hour',  # Very high rate for development
        'user': '3000/minute' if DEBUG else '2000/hour'  # Very high rate for development
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'UNAUTHENTICATED_USER': 'django.contrib.auth.models.AnonymousUser',
    'UNAUTHENTICATED_TOKEN': None,
    # Browsable API settings
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata',
    # Make browsable API more developer-friendly
    'HTML_SELECT_CUTOFF': 1000,
    'HTML_SELECT_CUTOFF_TEXT': "More than {count} items...",
    'URL_FORMAT_OVERRIDE': 'format',
    'FORMAT_SUFFIX_KWARG': 'format',
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
    'pragma',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]



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
    },
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': [] if DEBUG else ['broken_pipe_filter'],
        },
        'file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
            'filters': [] if DEBUG else ['broken_pipe_filter'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
        'filters': [] if DEBUG else ['broken_pipe_filter'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
            'filters': [] if DEBUG else ['broken_pipe_filter'],
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
            'filters': [] if DEBUG else ['broken_pipe_filter'],
        },
        'apps': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Performance settings - Optimized for faster responses
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', '5242880'))  # 5MB for faster processing
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', '5242880'))  # 5MB for faster processing


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
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
        '0.0.0.0',
    ]
    
    # Django Debug Toolbar configuration
    if 'debug_toolbar' in INSTALLED_APPS:
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
            'SHOW_COLLAPSED': True,
            'ENABLE_STACKTRACES': True,
        }
        
        DEBUG_TOOLBAR_PANELS = [
            'debug_toolbar.panels.history.HistoryPanel',
            'debug_toolbar.panels.versions.VersionsPanel',
            'debug_toolbar.panels.timer.TimerPanel',
            'debug_toolbar.panels.settings.SettingsPanel',
            'debug_toolbar.panels.headers.HeadersPanel',
            'debug_toolbar.panels.request.RequestPanel',
            'debug_toolbar.panels.sql.SQLPanel',
            'debug_toolbar.panels.staticfiles.StaticFilesPanel',
            'debug_toolbar.panels.templates.TemplatesPanel',
            'debug_toolbar.panels.cache.CachePanel',
            'debug_toolbar.panels.signals.SignalsPanel',
            'debug_toolbar.panels.redirects.RedirectsPanel',
            'debug_toolbar.panels.profiling.ProfilingPanel',
        ]

