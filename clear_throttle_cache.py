#!/usr/bin/env python
"""
Utility script to clear throttle cache and reset rate limits.
Run this when you're getting 429 Too Many Requests errors.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from django.core.cache import cache

def clear_throttle_cache():
    """Clear all throttle-related cache entries."""
    try:
        # Clear all cache entries (safe in development)
        cache.clear()
        print("✅ Throttle cache cleared successfully!")
        print("Rate limits have been reset. You should now be able to make API requests.")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

if __name__ == "__main__":
    clear_throttle_cache()
