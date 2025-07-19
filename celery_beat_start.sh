#!/bin/bash

# Enable error handling
set -euo pipefail

# Ensure environment variables are set
export DJANGO_SETTINGS_MODULE="adakings_backend.settings"

# Determine environment (dev/prod)
if [ "${RAILWAY_ENVIRONMENT:-}" = "production" ] || [ "${DJANGO_ENVIRONMENT:-}" = "production" ]; then
    export DJANGO_ENVIRONMENT="production"
    LOG_LEVEL="info"
else
    export DJANGO_ENVIRONMENT="development"
    LOG_LEVEL="debug"
fi

echo "=== Celery Beat Start ==="
echo "Environment: $DJANGO_ENVIRONMENT"
echo "Railway Environment: ${RAILWAY_ENVIRONMENT:-'Not Set'}"
echo "Redis URL: ${REDIS_URL:-'Not Set'}"
echo "Django Settings: $DJANGO_SETTINGS_MODULE"
echo "Log Level: $LOG_LEVEL"

echo "=== Running Django checks ==="
python manage.py check

echo "=== Running migrations for django-celery-beat ==="
python manage.py migrate django_celery_beat --noinput

echo "=== Starting Celery Beat Scheduler ==="
exec celery -A adakings_backend beat --loglevel=$LOG_LEVEL --scheduler django_celery_beat.schedulers:DatabaseScheduler
