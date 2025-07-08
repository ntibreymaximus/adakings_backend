from .settings import *

# Override settings for Railway Development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE', 'railway'),
        'USER': os.environ.get('PGUSER', 'postgres'),
        'PASSWORD': os.environ.get('PGPASSWORD', ''),
        'HOST': os.environ.get('PGHOST', 'localhost'),
        'PORT': os.environ.get('PGPORT', '5432'),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Debugging and Development settings
DEBUG = True
DJANGO_ENVIRONMENT = 'development'
ALLOWED_HOSTS = ['*']

# Middleware and installed apps are inherited from base settings

# Static and media files handling for Railway
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Additional configurations can be added below
