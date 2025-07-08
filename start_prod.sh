#!/bin/bash
set -e

echo "=== Production Django Backend Starting ==="
echo "PORT: $PORT"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Run migrations
python manage.py migrate

# Collect static files (without --noinput flag)  
python manage.py collectstatic --noinput --clear || python manage.py collectstatic --clear

# Start gunicorn
exec gunicorn adakings_backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
