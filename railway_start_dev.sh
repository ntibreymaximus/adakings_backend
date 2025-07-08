#!/bin/bash

# Railway Development Startup Script for Adakings Backend API
echo "Starting Adakings Backend - Development Environment\n"

export DJANGO_SETTINGS_MODULE=adakings_backend.settings_dev

# Wait for database to be ready
echo "Waiting for database to be ready..."
python -c "
import os
import time
import psycopg2
from psycopg2 import OperationalError

def wait_for_db():
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('PGHOST'),
                port=os.environ.get('PGPORT', 5432),
                user=os.environ.get('PGUSER'),
                password=os.environ.get('PGPASSWORD'),
                database=os.environ.get('PGDATABASE')
            )
            conn.close()
            print('Database is ready!')
            return
        except OperationalError:
            retry_count += 1
            print(f"Database not ready. Retry {retry_count}/{max_retries}...")
            time.sleep(2)
    
    print('Database connection failed after max retries')
    exit(1)

wait_for_db()"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if none exists
echo "Creating superuser if none exists..."
python manage.py create_superuser_if_none_exists

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the development server

echo "Development environment active.\n"

exec gunicorn adakings_backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --log-level debug \
    --access-logfile - \
    --error-logfile -
    --error-logfile -
