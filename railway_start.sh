#!/bin/bash

echo "=== Railway Deployment Start ==="
echo "Environment variables:"
echo "PORT: $PORT"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "DJANGO_DEBUG: $DJANGO_DEBUG"
echo "DATABASE_ENGINE: $DATABASE_ENGINE"
echo "All PG variables:"
env | grep PG || echo "No PG variables found"
echo "DATABASE_URL present: $([ -n "$DATABASE_URL" ] && echo "Yes" || echo "No")"
echo "All environment variables containing 'DATABASE':"
env | grep -i database || echo "No DATABASE variables found"
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

# Force PostgreSQL if PG variables are present
if [ -n "$PGDATABASE" ] || [ -n "$DATABASE_URL" ]; then
    echo "PostgreSQL variables detected - forcing DATABASE_ENGINE=postgresql"
    export DATABASE_ENGINE=postgresql
fi

echo "=== Running Django checks ==="
python manage.py check --deploy

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Starting Gunicorn ==="
exec gunicorn adakings_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 60 --access-logfile - --error-logfile -
