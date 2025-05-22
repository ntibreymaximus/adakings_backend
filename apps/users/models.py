from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser model to include
    role-based access control for the restaurant application.
    """
    # Role choices
    ADMIN = 'admin'
    FRONTDESK = 'frontdesk'
    KITCHEN = 'kitchen'
    DELIVERY = 'delivery'
    
    ROLE_CHOICES = [
        (ADMIN, _('Admin')),
        (FRONTDESK, _('Frontdesk Staff')),
        (KITCHEN, _('Kitchen Staff')),
        (DELIVERY, _('Delivery Staff')),
    ]
    
    # Role field
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=FRONTDESK,
        verbose_name=_('Role'),
        help_text=_('User role determines access permissions'),
    )
    
    # Additional fields
    staff_id = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Staff ID'),
        help_text=_('Unique identifier for staff members')
    )
    
    # Delivery-specific fields
    delivery_zone = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Delivery Zone'),
        help_text=_('Geographic area assigned for deliveries')
    )
    
    vehicle_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Vehicle Type'),
        help_text=_('Type of vehicle used for deliveries')
    )
    
    # Role check methods
    def is_admin(self):
        """Check if user has Admin role"""
        return self.role == self.ADMIN
    
    def is_frontdesk(self):
        """Check if user has Frontdesk Staff role"""
        return self.role == self.FRONTDESK
    
    def is_kitchen(self):
        """Check if user has Kitchen Staff role"""
        return self.role == self.KITCHEN
    
    def is_delivery(self):
        """Check if user has Delivery Staff role"""
        return self.role == self.DELIVERY
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
