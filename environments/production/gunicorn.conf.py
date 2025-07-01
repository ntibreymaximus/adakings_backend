# Gunicorn Configuration for Adakings Backend API - Production
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Preload app for better performance
preload_app = True

# User and group to run as
user = "www-data"
group = "www-data"

# Logging
loglevel = "warning"
errorlog = "/var/log/adakings/gunicorn_error.log"
accesslog = "/var/log/adakings/gunicorn_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "adakings_backend"

# Server mechanics
daemon = False
pidfile = "/var/run/adakings/gunicorn.pid"
tmp_upload_dir = "/tmp"

# SSL (if terminating SSL at Gunicorn level, usually handled by Nginx)
# keyfile = "/etc/ssl/private/yourdomain.key"
# certfile = "/etc/ssl/certs/yourdomain.crt"

# Environment variables
raw_env = [
    "DJANGO_SETTINGS_MODULE=adakings_backend.settings",
    "DJANGO_ENVIRONMENT=production",
]

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Adakings Backend API in production mode")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Adakings Backend API workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker {worker.age} spawned (pid: {worker.pid})")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.age} spawned (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
