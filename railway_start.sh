#!/bin/bash

# Enable error handling
set -euo pipefail

# Ensure production environment variables are set
export DJANGO_DEBUG="False"
export DJANGO_SETTINGS_MODULE="adakings_backend.settings"
export DJANGO_ENVIRONMENT="production"
export DATABASE_ENGINE="postgresql"

echo "=== Railway Deployment Start (Production) ==="
echo "Verifying Environment Configuration:"
echo "PORT: $PORT"
echo "DATABASE_ENGINE: $DATABASE_ENGINE"
echo "PGHOST/DB_HOST: ${PGHOST:-$DB_HOST}"
echo "PGDATABASE/DB_NAME: ${PGDATABASE:-$DB_NAME}"
echo "DJANGO_DEBUG: $DJANGO_DEBUG"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "DJANGO_ENVIRONMENT: $DJANGO_ENVIRONMENT"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-'Not Set'}"
echo "PYTHONPATH: ${PYTHONPATH:-'Not Set'}"

echo "=== Testing Django import ==="
python -c "import django; print(f'Django version: {django.get_version()}')"

echo "=== Testing settings import ==="
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings'); import django; django.setup(); print('Settings imported successfully')"

echo "=== Verifying Environment Configuration ==="
python check_environment.py

echo "=== Running Django checks ==="
python manage.py check
if [ $? -ne 0 ]; then
    echo "Django checks failed!"
    exit 1
fi

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear
if [ $? -ne 0 ]; then
    echo "Static files collection failed!"
    exit 1
fi

echo "=== Running migrations ==="
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo "Migrations failed!"
    exit 1
fi

echo "=== Creating superuser if needed ==="
python manage.py create_superuser_if_none_exists || echo "Superuser creation skipped (may already exist)"

echo "=== Testing WSGI application ==="
python -c "from adakings_backend.wsgi import application; print('WSGI application loaded successfully')"
if [ $? -ne 0 ]; then
    echo "WSGI application test failed!"
    exit 1
fi

echo "=== Starting Gunicorn with enhanced logging ==="
exec gunicorn adakings_backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class sync \
    --timeout 60 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload
