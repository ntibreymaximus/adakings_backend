"""
Settings package for Adakings Backend API

Environment-specific settings loading:
- production.py: Production environment
- development.py: Development environment  
- base.py: Shared base settings
"""

import os

# Default to development if no environment is specified
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
    print("🚀 Production environment loaded")
elif ENVIRONMENT == 'development':
    from .development import *  
    print("🔧 Development environment loaded")
else:
    # Fallback to development for any other value
    from .development import *
    print("⚠️  Unknown environment '{}', falling back to development".format(ENVIRONMENT))