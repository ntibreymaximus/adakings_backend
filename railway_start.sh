#!/bin/bash

echo "=== Railway Deployment Start ==="
echo "Environment variables:"
echo "PORT: $PORT"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "DJANGO_DEBUG: $DJANGO_DEBUG"
echo "DATABASE_ENGINE: $DATABASE_ENGINE"

echo "=== Running Django checks ==="
python manage.py check --deploy

echo "=== Starting Gunicorn ==="
exec gunicorn adakings_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 60 --access-logfile - --error-logfile -
