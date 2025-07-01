# Gunicorn configuration for Adakings Backend API - Production Environment
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes (optimized for production)
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 100

# Logging (production-specific paths)
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Process naming
proc_name = "adakings_backend"

# Server mechanics
daemon = False
pidfile = "logs/gunicorn.pid"
user = "adakings"
group = "adakings"
tmp_upload_dir = None

# Worker process lifecycle
preload_app = True
reload = False  # No auto-reload in production

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("🚀 Adakings Backend API server is ready. Listening on %s", bind)

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("🔄 Worker received INT or QUIT signal")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("🛑 Adakings Backend API server is shutting down")

# Environment variables for Django
raw_env = [
    'DJANGO_SETTINGS_MODULE=adakings_backend.settings.production',
    'DJANGO_ENVIRONMENT=production',
]
