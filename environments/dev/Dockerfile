# Dockerfile for Adakings Backend API - Development Environment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=adakings_backend.settings.dev
ENV DJANGO_ENVIRONMENT=dev

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
        vim \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY environments/dev/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/staticfiles /app/mediafiles

# Create non-root user
RUN groupadd -r adakings && useradd -r -g adakings adakings
RUN chown -R adakings:adakings /app
USER adakings

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health/ || exit 1

# Run gunicorn
CMD ["gunicorn", "-c", "environments/dev/gunicorn.conf.py", "adakings_backend.wsgi:application"]
