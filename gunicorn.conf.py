# Gunicorn configuration for Adakings Backend API - Dev Environment
import multiprocessing
import os
import signal
import logging

# Server socket
bind = "0.0.0.0:8001"  # Different port for dev
backlog = 4096  # Increased to handle more connections in production
reuse_port = True  # Enable socket reuse for better performance

# Worker processes - optimized for production
workers = max(2, min(multiprocessing.cpu_count() * 2 + 1, 8))
worker_class = "gevent"  # Better for I/O bound operations and WebSocket proxying
worker_connections = 2000  # Increased connections per worker
timeout = 180  # Increased timeout to handle slow requests and WebSocket upgrades
keepalive = 10  # Longer keepalive for better connection reuse
graceful_timeout = 60  # More time for graceful worker shutdown

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

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("🚨 DEV Worker aborted")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("🔧 Worker about to be forked (PID: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("✅ Worker forked (PID: %s)", worker.pid)
    
    # Ignore SIGPIPE to prevent broken pipe errors from crashing workers
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

def on_exit(server):
    """Called just before exiting."""
    server.log.info("🛑 Adakings Backend API DEV server is shutting down")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("🔄 Reloading Adakings Backend API DEV server")

# Environment variables for Django
raw_env = [
    'DJANGO_SETTINGS_MODULE=adakings_backend.settings.settings',
    'DJANGO_ENVIRONMENT=dev',
    'PYTHONUNBUFFERED=1',  # Ensure output is not buffered
]

# Error handling
def handle_worker_exception(worker, req, client, exc):
    """Handle worker exceptions gracefully."""
    if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
        # Log broken pipe errors but don't crash the worker
        worker.log.warning(f"Client disconnected: {exc}")
        return
    
    # For other exceptions, log and let gunicorn handle them
    worker.log.error(f"Worker exception: {exc}", exc_info=True)
