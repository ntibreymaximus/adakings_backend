# Gunicorn configuration for Adakings Backend API - Dev Environment
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8001"  # Different port for dev
backlog = 512

# Worker processes (fewer for dev environment)
workers = max(2, multiprocessing.cpu_count())
worker_class = "sync"
worker_connections = 500
timeout = 60  # Longer timeout for debugging
keepalive = 2

# Restart workers after this many requests
max_requests = 500
max_requests_jitter = 50

# Logging (dev-specific paths)
accesslog = "logs/dev_gunicorn_access.log"
errorlog = "logs/dev_gunicorn_error.log"
loglevel = "debug"  # More verbose logging for dev
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Process naming
proc_name = "adakings_backend_dev"

# Server mechanics
daemon = False
pidfile = "logs/dev_gunicorn.pid"
# No user/group restrictions for dev environment
tmp_upload_dir = None

# Worker process lifecycle
preload_app = True
reload = True  # Enable auto-reload for development

# Security (relaxed for dev)
limit_request_line = 8192
limit_request_fields = 200
limit_request_field_size = 16380

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("🔧 Adakings Backend API DEV server is ready. Listening on %s", bind)

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("🔄 DEV Worker received INT or QUIT signal")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("🛑 Adakings Backend API DEV server is shutting down")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("🔄 Reloading Adakings Backend API DEV server")

# Environment variables for Django
raw_env = [
    'DJANGO_SETTINGS_MODULE=adakings_backend.settings.dev',
    'DJANGO_ENVIRONMENT=dev',
]
