#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Module-level flag to prevent duplicate environment checks
_env_check_done = False

def main():
    """Run administrative tasks."""
    global _env_check_done
    
    # Set default settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
    
    # Run environment check before starting the server (only once)
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver' and not _env_check_done:
        _env_check_done = True
        print("🔍 Running environment configuration check...")
        print("-" * 50)
        try:
            from check_environment import check_environment
            validation_passed, env_type = check_environment()
            
            if not validation_passed:
                print("\n❌ Environment validation failed! Please fix the issues above.")
                sys.exit(1)
            
            print(f"\n✅ Environment check passed for {env_type}!")
            print("🚀 Starting Django development server...")
            print("=" * 50)
            
        except Exception as e:
            print(f"\n⚠️  Warning: Environment check failed: {e}")
            print("⚠️  Proceeding with server start anyway...")
            print("=" * 50)
    
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
