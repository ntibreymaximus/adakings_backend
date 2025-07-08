# Dockerfile for Adakings Backend API - Production Environment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=adakings_backend.settings
ENV DJANGO_ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/staticfiles /app/mediafiles

# Fix line endings and make startup scripts executable
RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*
RUN dos2unix railway_start.sh railway_start_dev.sh start_prod.sh entrypoint.sh
RUN chmod +x railway_start.sh railway_start_dev.sh start_prod.sh entrypoint.sh

# Verify scripts exist and are executable
RUN ls -la /app/railway_start*.sh /app/entrypoint.sh && file /app/railway_start*.sh /app/entrypoint.sh

# Create non-root user
RUN groupadd -r adakings && useradd -r -g adakings adakings
RUN chown -R adakings:adakings /app
USER adakings

# Note: collectstatic will be run during startup when environment variables are available

# Expose port
EXPOSE $PORT


# Use entrypoint.sh to determine which startup script to use
CMD ["./entrypoint.sh"]
