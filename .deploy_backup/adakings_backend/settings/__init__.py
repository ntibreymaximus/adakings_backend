"""
Settings package for Adakings Backend API

Environment-specific settings loading:
- production.py: Production environment
- dev.py: Development environment (production-like with dev values)
- development.py: Local development environment  
- base.py: Shared base settings
"""

import os

# Default to development if no environment is specified
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

# Only print environment info once from __init__.py if not already loaded
if ENVIRONMENT == 'production':
    from .production import *
    if not os.environ.get('DJANGO_SETTINGS_LOADED'):
        print("🚀 Production environment loaded")
elif ENVIRONMENT == 'dev':
    from .dev import *
    if not os.environ.get('DJANGO_SETTINGS_LOADED'):
        print("🔧 Dev environment loaded (production-like with dev values)")
elif ENVIRONMENT == 'development':
    from .development import *  
    if not os.environ.get('DJANGO_SETTINGS_LOADED'):
        print("🔧 Development environment loaded (local development)")
else:
    # Fallback to development for any other value
    from .development import *
    if not os.environ.get('DJANGO_SETTINGS_LOADED'):
        print("⚠️  Unknown environment '{}', falling back to development".format(ENVIRONMENT))
