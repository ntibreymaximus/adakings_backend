#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    
    # Handle environment-specific runserver commands
    if len(sys.argv) >= 3 and sys.argv[1] == 'runserver':
        env_arg = sys.argv[2].lower()
        
        if env_arg in ['local', 'dev', 'prod']:
            # Set environment variables based on argument
            if env_arg == 'local':
                # Set the .env file path to feature environment
                from pathlib import Path
                BASE_DIR = Path(__file__).resolve().parent
                os.environ['DOTENV_PATH'] = str(BASE_DIR / 'environments/feature/.env')
                os.environ['DJANGO_ENVIRONMENT'] = 'development'
                os.environ['DJANGO_SETTINGS_MODULE'] = 'adakings_backend.settings.development'
                print("🔧 Starting server in LOCAL environment (development settings)")
            elif env_arg == 'dev':
                # Set the .env file path to dev environment
                from pathlib import Path
                BASE_DIR = Path(__file__).resolve().parent
                os.environ['DOTENV_PATH'] = str(BASE_DIR / 'environments/dev/.env')
                os.environ['DJANGO_ENVIRONMENT'] = 'dev'
                os.environ['DJANGO_SETTINGS_MODULE'] = 'adakings_backend.settings.dev'
                print("🔧 Starting server in DEV environment (production-like settings)")
            elif env_arg == 'prod':
                # Set the .env file path to production environment
                from pathlib import Path
                BASE_DIR = Path(__file__).resolve().parent
                os.environ['DOTENV_PATH'] = str(BASE_DIR / 'environments/production/.env')
                os.environ['DJANGO_ENVIRONMENT'] = 'production'
                os.environ['DJANGO_SETTINGS_MODULE'] = 'adakings_backend.settings.production'
                print("🚀 Starting server in PROD environment (production settings)")
            
            # Remove the environment argument and run normal runserver
            sys.argv.pop(2)  # Remove the environment argument
            
            # Add default port if not specified
            if len(sys.argv) == 2:  # Only 'manage.py runserver' left
                sys.argv.append('8000')
    
    # Set default settings module if not already set
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
