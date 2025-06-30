"""
Settings package for Adakings Backend API

Environment-specific settings loading:
- production.py: Production environment
- dev_test.py: Dev-Test environment (production-like with test values)
- development.py: Development environment  
- base.py: Shared base settings
"""

import os

# Default to dev-test if no environment is specified
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'dev-test')

if ENVIRONMENT == 'production':
    from .production import *
    print("🚀 Production environment loaded")
elif ENVIRONMENT == 'dev-test':
    from .dev_test import *
    print("🧪 Dev-Test environment loaded")
elif ENVIRONMENT == 'development':
    from .development import *  
    print("🔧 Development environment loaded")
else:
    # Fallback to dev-test for any other value
    from .dev_test import *
    print("⚠️  Unknown environment '{}', falling back to dev-test".format(ENVIRONMENT))
