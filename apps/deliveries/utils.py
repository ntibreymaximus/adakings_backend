import os
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


def get_file_hash(file_path):
    """Generate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None


def check_and_reload_delivery_locations():
    """Check if delivery locations file has changed and reload if necessary"""
    file_path = os.path.join(settings.BASE_DIR, 'delivery_locations.txt')
    cache_key = 'delivery_locations_file_hash'
    
    if not os.path.exists(file_path):
        logger.warning(f"Delivery locations file not found: {file_path}")
        return False
    
    # Get current file hash
    current_hash = get_file_hash(file_path)
    if not current_hash:
        return False
    
    # Get cached hash
    cached_hash = cache.get(cache_key)
    
    # If hash changed or not cached, reload locations
    if cached_hash != current_hash:
        try:
            logger.info("Delivery locations file changed, reloading...")
            call_command('load_delivery_locations', '--update')
            
            # Update cached hash
            cache.set(cache_key, current_hash, timeout=None)
            logger.info("Delivery locations reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading delivery locations: {e}")
            return False
    
    return False


def ensure_delivery_locations_loaded():
    """Ensure delivery locations are loaded in the database"""
    from .models import DeliveryLocation
    
    # Check if any locations exist
    if DeliveryLocation.objects.count() == 0:
        logger.info("No delivery locations found, loading from file...")
        try:
            call_command('load_delivery_locations')
            return True
        except Exception as e:
            logger.error(f"Error loading delivery locations: {e}")
            return False
    
    # Check if file has been modified
    return check_and_reload_delivery_locations()
