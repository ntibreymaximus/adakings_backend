#!/bin/bash

# Enable error handling
set -euo pipefail

echo "=== Railway Deployment Start ==="
echo "Environment variables:"
echo "PORT: $PORT"
echo "DATABASE_ENGINE: $DATABASE_ENGINE"
echo "DB_HOST: $DB_HOST"
echo "DB_NAME: $DB_NAME"
echo "DJANGO_DEBUG: $DJANGO_DEBUG"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "PYTHON_PATH: $PYTHONPATH"

echo "=== Testing Django import ==="
python -c "import django; print(f'Django version: {django.get_version()}')"

echo "=== Testing settings import ==="
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings'); import django; django.setup(); print('Settings imported successfully')"

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
    --workers 1 \
    --timeout 60 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output
