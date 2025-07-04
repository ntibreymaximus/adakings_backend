#!/usr/bin/env python
"""
Enhanced startup script for Adakings Backend with broken pipe error handling.
"""
import os
import sys
import signal
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_signal_handlers():
    """Set up signal handlers to gracefully handle interruptions."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ignore SIGPIPE to prevent broken pipe errors
    if hasattr(signal, 'SIGPIPE'):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)

def check_environment():
    """Check if the environment is properly set up."""
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        logger.warning(".env file not found. Using default environment variables.")
    
    # Check if logs directory exists
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Check if requirements are installed
    try:
        import django
        logger.info(f"Django version: {django.get_version()}")
    except ImportError:
        logger.error("Django not found. Please install requirements: pip install -r requirements.txt")
        sys.exit(1)

def run_migrations():
    """Run database migrations."""
    try:
        logger.info("Running database migrations...")
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Migration failed: {result.stderr}")
            return False
        
        logger.info("Migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False

def start_django_server(port=8000, use_daphne=False):
    """Start the Django development server or Daphne ASGI server."""
    try:
        if use_daphne:
            # Use Daphne for ASGI with WebSocket support
            logger.info(f"Starting Daphne ASGI server on port {port}...")
            cmd = [
                sys.executable, '-m', 'daphne',
                '-p', str(port),
                '-b', '0.0.0.0',
                '--access-log', 'logs/daphne_access.log',
                '--verbosity', '2',
                'adakings_backend.asgi:application'
            ]
        else:
            # Use Django development server with optimized settings
            logger.info(f"Starting Django development server on port {port}...")
            cmd = [
                sys.executable, 'manage.py', 'runserver',
                f'0.0.0.0:{port}',
                '--nothreading',  # Disable threading for better auto-reload stability
                '--noreload' if os.environ.get('DISABLE_AUTO_RELOAD', 'False').lower() == 'true' else '--settings=adakings_backend.settings.settings'
            ]
        
        # Set environment variables to handle broken pipes and optimize auto-reload
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent .pyc files
        env['DJANGO_SETTINGS_MODULE'] = 'adakings_backend.settings.settings'
        env['DJANGO_AUTORELOAD_POLL_INTERVAL'] = '2'  # Slower polling for stability
        
        # Add Windows-specific optimizations
        if os.name == 'nt':  # Windows
            env['PYTHONIOENCODING'] = 'utf-8'
            env['DJANGO_AUTORELOAD_USE_POLLING'] = 'True'  # Force polling on Windows
        
        # Start the server
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor the server output with error handling
        restart_count = 0
        max_restarts = 3
        
        try:
            for line in process.stdout:
                line = line.strip()
                if line:  # Only print non-empty lines
                    print(line)
                    
                    # Check for specific error patterns
                    if 'Broken pipe' in line:
                        logger.warning("Broken pipe detected - client disconnected")
                    elif 'ConnectionResetError' in line:
                        logger.warning("Connection reset by peer")
                    elif 'BrokenPipeError' in line:
                        logger.warning("Broken pipe error - handling gracefully")
                    elif 'autoreload' in line.lower() and 'error' in line.lower():
                        logger.warning(f"Auto-reload issue detected: {line}")
                        restart_count += 1
                        if restart_count >= max_restarts:
                            logger.error("Too many auto-reload failures. Consider disabling auto-reload.")
                            
        except UnicodeDecodeError as e:
            logger.warning(f"Unicode decode error in server output: {e}")
        except Exception as e:
            logger.error(f"Error reading server output: {e}")
        
        process.wait()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        if 'process' in locals():
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Forcing server shutdown...")
                process.kill()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

def start_gunicorn_server(port=8001):
    """Start the Gunicorn server with improved error handling."""
    try:
        logger.info(f"Starting Gunicorn server on port {port}...")
        
        cmd = [
            sys.executable, '-m', 'gunicorn',
            '--config', 'gunicorn.conf.py',
            'adakings_backend.wsgi:application'
        ]
        
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['DJANGO_SETTINGS_MODULE'] = 'adakings_backend.settings.settings'
        
        # Start Gunicorn
        subprocess.run(cmd, env=env)
        
    except KeyboardInterrupt:
        logger.info("Gunicorn server shutdown requested by user")
    except Exception as e:
        logger.error(f"Error starting Gunicorn: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start Adakings Backend Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--server', choices=['django', 'daphne', 'gunicorn'], 
                       default='django', help='Server type to use')
    parser.add_argument('--no-migrate', action='store_true', 
                       help='Skip running migrations')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    setup_signal_handlers()
    
    # Check environment
    check_environment()
    
    # Run migrations unless skipped
    if not args.no_migrate:
        if not run_migrations():
            logger.error("Failed to run migrations. Exiting.")
            sys.exit(1)
    
    # Start the appropriate server
    if args.server == 'django':
        start_django_server(args.port)
    elif args.server == 'daphne':
        start_django_server(args.port, use_daphne=True)
    elif args.server == 'gunicorn':
        start_gunicorn_server(args.port)

if __name__ == '__main__':
    main()
