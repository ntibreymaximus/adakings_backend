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

from .settings import *
print("Unified environment loaded") # Now a single settings file is used
