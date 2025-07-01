"""
Settings package for Adakings Backend API

Environment-specific settings loading:
- production.py: Production environment
- dev.py: Development environment similar to production
- development.py: Local development environment
- base.py: Shared base settings
"""

import os

# Default to development for feature branches
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
    print("🚀 Production environment loaded")
elif ENVIRONMENT == 'dev':
    from .dev import *
    print("🔧 Dev environment loaded")
elif ENVIRONMENT == 'development':
    from .development import *  
    print("🔧 Development environment loaded (feature branch)")
else:
    # Fallback to development for feature branches
    from .development import *
    print("⚠️  Unknown environment '{}', falling back to development".format(ENVIRONMENT))