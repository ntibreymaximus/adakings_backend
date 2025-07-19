#!/bin/bash

# Universal entrypoint script for Railway services
set -euo pipefail

echo "=== Railway Service Entrypoint ==="

# Get the service name from Railway environment
SERVICE_NAME="${RAILWAY_SERVICE_NAME:-web}"
echo "Service Name: $SERVICE_NAME"
echo "Environment: ${DJANGO_ENVIRONMENT:-production}"

# Check if we're in the correct working directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Are we in the correct directory?"
    ls -la
    exit 1
fi

# Route to appropriate start script based on service name
case "$SERVICE_NAME" in
    "celery-worker")
        echo "=== Starting Celery Worker ==="
        exec bash celery_worker_start.sh
        ;;
    "celery-beat")
        echo "=== Starting Celery Beat ==="
        exec bash celery_beat_start.sh
        ;;
    *)
        # Default to web service
        echo "=== Starting Web Service ==="
        if [ "${DJANGO_ENVIRONMENT:-}" = "production" ] || [ "${RAILWAY_ENVIRONMENT:-}" = "prod" ]; then
            exec bash railway_start.sh
        else
            exec bash railway_start_dev.sh
        fi
        ;;
esac
