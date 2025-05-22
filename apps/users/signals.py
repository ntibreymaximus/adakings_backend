import random
import string
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime

from .models import CustomUser

@receiver(pre_save, sender=CustomUser)
def generate_staff_id(sender, instance, **kwargs):
    """
    Generate a unique staff ID if one is not provided.
    Format: [Role Prefix][Year][Random 4 digits]
    """
    # Only generate staff_id if it's not already set
    if not instance.staff_id:
        # Get prefix based on role
        role_prefix = {
            'admin': 'A',
            'frontdesk': 'F',
            'kitchen': 'K',
            'delivery': 'D'
        }.get(instance.role, 'S')  # S for staff if role not recognized
        
        # Get current year's last two digits
        year = str(timezone.now().year)[-2:]
        
        # Generate random 4-digit number
        random_digits = ''.join(random.choices(string.digits, k=4))
        
        # Create staff ID
        staff_id = f"{role_prefix}{year}{random_digits}"
        
        # Check for uniqueness (very unlikely to have a collision, but just to be safe)
        while CustomUser.objects.filter(staff_id=staff_id).exists():
            random_digits = ''.join(random.choices(string.digits, k=4))
            staff_id = f"{role_prefix}{year}{random_digits}"
        
        instance.staff_id = staff_id

@receiver(post_save, sender=CustomUser)
def setup_role_specific_settings(sender, instance, created, **kwargs):
    """
    Handle role-specific setup after a user is created or updated.
    - For admins: Set is_staff and is_superuser appropriately
    - For other roles: Set appropriate permissions
    """
    if created:  # Only run this for newly created users
        # Admin users should be staff users by default
        if instance.role == 'admin' and not instance.is_staff:
            instance.is_staff = True
            instance.save(update_fields=['is_staff'])

