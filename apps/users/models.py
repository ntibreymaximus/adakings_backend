from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    """
    Custom user manager to handle superuser creation with proper role assignment.
    """
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Create and save a superuser with admin role and the given username, email, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')  # Set role to superadmin for superusers
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser model to include
    role-based access control for the restaurant application.
    """
    # Role choices
    SUPERADMIN = 'superadmin'
    ADMIN = 'admin'
    FRONTDESK = 'frontdesk'
    KITCHEN = 'kitchen'
    DELIVERY = 'delivery'
    
    ROLE_CHOICES = [
        (SUPERADMIN, _('Superadmin')),
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
        max_length=10,      # Suitable for "ADAUG-XXXX" (e.g., ADAUG-9999)
        unique=True,
        editable=False,     # Not manually editable
        verbose_name=_('Staff ID'),
        help_text=_('Auto-generated unique identifier for staff members (ADAUG-XXX)')
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
    
    # Custom manager
    objects = CustomUserManager()
    
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
    
    def is_superadmin(self):
        """Check if user has Superadmin role"""
        return self.role == self.SUPERADMIN
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def clean(self):
        """
        Validate that superadmin role is only assigned to superusers.
        """
        from django.core.exceptions import ValidationError
        
        # Ensure only superusers can have superadmin role
        if self.role == self.SUPERADMIN and not self.is_superuser:
            raise ValidationError({
                'role': 'Superadmin role can only be assigned to superusers.'
            })
        
        # Ensure superusers have superadmin role
        if self.is_superuser and self.role != self.SUPERADMIN:
            # Allow this but automatically correct it
            self.role = self.SUPERADMIN
    
    def save(self, *args, **kwargs):
        # Run validation
        self.clean()
        
        # Auto-generate staff_id for new users
        if not self.pk and not self.staff_id:  # If new user and staff_id is not already set
            prefix = "ADAUG-"
            last_staff_member = CustomUser.objects.filter(staff_id__startswith=prefix).order_by('staff_id').last()
            
            if last_staff_member and last_staff_member.staff_id:
                try:
                    last_number_str = last_staff_member.staff_id.split(prefix)[-1]
                    last_number = int(last_number_str)
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    # Fallback if parsing fails (e.g., old data not matching pattern)
                    new_number = CustomUser.objects.filter(staff_id__startswith=prefix).count() + 1
            else:
                new_number = 1
            
            # Format to ensure it's at least 3 digits, e.g., ADAUG-001
            # If new_number can exceed 999, adjust formatting (e.g. :04d) and max_length of field
            self.staff_id = f"{prefix}{new_number:03}"
            
            # Ensure uniqueness if a race condition occurs (highly unlikely for typical loads)
            # or if the count-based fallback was used and wasn't perfectly sequential.
            while CustomUser.objects.filter(staff_id=self.staff_id).exists():
                new_number += 1
                self.staff_id = f"{prefix}{new_number:03}"
        
        # Automatically set is_staff based on role
        # Only superadmins (who are also superusers) have Django admin access (is_staff=True)
        # All other roles (including admin) use API only (is_staff=False)
        
        if self.is_superuser and self.role == self.SUPERADMIN:
            # Only superadmins have Django admin access
            self.is_staff = True
        else:
            # All other roles (including admin) should NOT have Django admin access
            # Admin role users use the API interface, not Django admin
            self.is_staff = False
            if not hasattr(self, '_skip_superuser_check'):
                self.is_superuser = False

        super().save(*args, **kwargs)
