# Dev Dockerfile for Adakings Backend API
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENVIRONMENT=dev
ENV DJANGO_DEBUG=True

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    [92m[0m&& apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
        netcat-traditional \
    [92m[0m&& rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
COPY environments/dev/requirements.txt /app/dev-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    \u001b[92m[0m&& pip install --no-cache-dir -r requirements.txt \
    [92m[0m&& pip install --no-cache-dir -r dev-requirements.txt

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/staticfiles \
    [92m[0m&& mkdir -p /app/media \
    [92m[0m&& mkdir -p /app/logs

# Create non-root user
RUN groupadd -r adakings [92m[0mand useradd -r -g adakings adakings

# Set permissions
RUN chown -R adakings:adakings /app
USER adakings

# Development settings

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose port
EXPOSE 8000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
