import os
import hashlib
from datetime import datetime
from django.core.cache import cache
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

MENU_CACHE_KEY = 'menu_items_file_checksum'


def perform_menu_sync(clear_old=False):
    """Synchronize menu items from file"""
    try:
        if clear_old:
            logger.info("Clearing old menu items...")
        
        call_command('load_menu_items', '--update')
        logger.info("Menu items synchronized successfully")
    except Exception as e:
        logger.error(f"Error synchronizing menu items: {e}")


def menu_file_has_changed(file_path):
    """Check if the menu file has changed"""
    # Compute checksum of the file
    if not os.path.exists(file_path):
        logger.warning("Menu file not found")
        return False
    
    file_checksum = compute_file_checksum(file_path)
    cached_checksum = cache.get(MENU_CACHE_KEY)
    
    if cached_checksum != file_checksum:
        # Update cache with new checksum
        cache.set(MENU_CACHE_KEY, file_checksum, timeout=None)
        return True
        
    return False


def compute_file_checksum(file_path):
    """Compute and return the checksum of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
