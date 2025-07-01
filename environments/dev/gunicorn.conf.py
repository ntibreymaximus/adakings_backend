# Gunicorn Configuration for Adakings Backend API - Development Environment
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 512

# Worker processes (fewer for development)
workers = max(2, multiprocessing.cpu_count())
worker_class = "sync"
worker_connections = 500
timeout = 60  # Longer timeout for debugging
keepalive = 2

# Restart workers more frequently for development
max_requests = 500
max_requests_jitter = 25

# Preload app for consistency with production
preload_app = True

# User and group (development)
user = "www-data"
group = "www-data"

# Logging (more verbose for development)
loglevel = "info"
errorlog = "/var/log/adakings/dev_gunicorn_error.log"
accesslog = "/var/log/adakings/dev_gunicorn_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "adakings_backend_dev"

# Server mechanics
daemon = False
pidfile = "/var/run/adakings/dev_gunicorn.pid"
tmp_upload_dir = "/tmp"

# Development settings
reload = True  # Auto-reload on code changes
reload_extra_files = [
    "/var/www/adakings/adakings_backend/settings/",
    "/var/www/adakings/apps/",
]

# Environment variables
raw_env = [
    "DJANGO_SETTINGS_MODULE=adakings_backend.settings",
    "DJANGO_ENVIRONMENT=dev",
]

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Adakings Backend API in development mode")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Adakings Backend API workers (dev environment)")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Development worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Development worker {worker.age} spawned (pid: {worker.pid})")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Development worker {worker.age} ready (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.warning("Development worker received SIGABRT signal")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("Shutting down Adakings Backend API development server")
