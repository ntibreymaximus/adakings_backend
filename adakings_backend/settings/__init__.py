"""
Dev Settings for Adakings Backend API

This dev branch uses production-like configuration but with development values.
Similar to production but safe for development work.
"""

import os

# Default to dev for this branch
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'dev')

if ENVIRONMENT == 'production':
    from .production import *
    print("🚀 Production environment loaded")
elif ENVIRONMENT == 'dev':
    from .dev import *
    print("🔧 Dev environment loaded (dev branch)")
elif ENVIRONMENT == 'development':
    from .development import *  
    print("🔧 Development environment loaded")
else:
    # Fallback to dev for this branch
    from .dev import *
    print("⚠️  Unknown environment '{}', falling back to dev".format(ENVIRONMENT))