#!/bin/bash

echo "=== Railway Deployment Start ==="
echo "Environment variables:"
echo "PORT: $PORT"
echo "DATABASE_ENGINE: $DATABASE_ENGINE"
echo "DB_HOST: $DB_HOST"
echo "DB_NAME: $DB_NAME"
echo "DJANGO_DEBUG: $DJANGO_DEBUG"

echo "=== Running Django checks ==="
python manage.py check --deploy

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Starting Gunicorn ==="
exec gunicorn adakings_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 60 --access-logfile - --error-logfile -
