from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import MenuItem
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=MenuItem)
def ensure_menu_item_prefix(sender, instance, **kwargs):
    """
    Ensure that bolt menu items always have their prefixes.
    This acts as a safety net in case items are created outside the serializer.
    """
    if instance.item_type == 'bolt':
        # Clean any existing prefix first
        clean_name = instance.name
        if clean_name.startswith('BOLT-'):
            clean_name = clean_name[5:]
        
        # Add the prefix
        if not instance.name.startswith('BOLT-'):
            instance.name = f'BOLT-{clean_name}'
            logger.info(f"Signal: Added BOLT prefix to '{clean_name}'")
    
