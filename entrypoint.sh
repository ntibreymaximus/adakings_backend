#!/bin/bash

# Entrypoint script for Adakings Backend API
set -euo pipefail

echo "=== Adakings Backend Entrypoint ==="

# Check if we're in the correct working directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Are we in the correct directory?"
    ls -la
    exit 1
fi

# Verify required scripts exist
REQUIRED_SCRIPTS=("railway_start.sh" "railway_start_dev.sh")
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -f "$script" ]; then
        echo "Error: Required script $script not found!"
        ls -la *.sh
        exit 1
    fi
    
    if [ ! -x "$script" ]; then
        echo "Error: Script $script is not executable!"
        ls -la "$script"
        exit 1
    fi
done

# Check environment variables
echo "Environment Variables:"
echo "DJANGO_ENVIRONMENT: ${DJANGO_ENVIRONMENT:-'Not Set'}"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-'Not Set'}"
echo "PORT: ${PORT:-'Not Set'}"

# Determine which startup script to use
if [ "${DJANGO_ENVIRONMENT:-}" = "production" ] || [ "${RAILWAY_ENVIRONMENT:-}" = "production" ]; then
    echo "=== Starting Production Environment ==="
    exec ./railway_start.sh
else
    echo "=== Starting Development Environment ==="
    exec ./railway_start_dev.sh
fi
