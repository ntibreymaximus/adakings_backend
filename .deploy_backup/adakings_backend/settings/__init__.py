"""
Dev-Test Settings for Adakings Backend API

This dev-test branch uses production-like configuration with test/placeholder values.
Safe for testing production scenarios without real data/keys.
"""

import os

# Default to dev-test for this branch
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'dev-test')

if ENVIRONMENT == 'production':
    from .production import *
    print("🚀 Production environment loaded")
elif ENVIRONMENT == 'dev-test':
    from .dev_test import *
    print("🧪 Dev-Test environment loaded (dev-test branch)")
elif ENVIRONMENT == 'development':
    from .development import *  
    print("🔧 Development environment loaded")
else:
    # Fallback to dev-test for this branch
    from .dev_test import *
    print("⚠️  Unknown environment '{}', falling back to dev-test".format(ENVIRONMENT))