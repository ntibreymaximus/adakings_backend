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

echo "=== Testing ASGI application ==="
python -c "from adakings_backend.asgi import application; print('ASGI application loaded successfully')"
if [ $? -ne 0 ]; then
    echo "ASGI application test failed!"
    exit 1
fi

echo "=== Starting Daphne for WebSocket support ==="
exec daphne \
    -b 0.0.0.0 \
    -p $PORT \
    --access-log - \
    -v 2 \
    adakings_backend.asgi:application
