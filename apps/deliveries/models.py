from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class DeliveryLocation(models.Model):
    """Model for managing delivery locations and their fees"""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the delivery location"
    )
    fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Delivery fee for this location"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this location is currently available for delivery"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Location"
        verbose_name_plural = "Delivery Locations"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} (₵{self.fee:.2f})"
    
    @classmethod
    def get_active_locations_dict(cls):
        """Return a dictionary of active locations with their fees"""
        return {loc.name: loc.fee for loc in cls.objects.filter(is_active=True)}


class DeliveryRider(models.Model):
    """Model for delivery riders"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('busy', 'Busy'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_orders = models.IntegerField(default=0)
    total_deliveries = models.IntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=5.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_available = models.BooleanField(default=True)
    max_concurrent_orders = models.IntegerField(default=3)
    
    class Meta:
        ordering = ['-rating', 'current_orders']
        indexes = [
            models.Index(fields=['status', 'is_available']),
            models.Index(fields=['current_orders']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.phone}"
    
    @property
    def can_accept_orders(self):
        return (
            self.status == 'active' and 
            self.is_available and 
            self.current_orders < self.max_concurrent_orders
        )
    


class OrderAssignment(models.Model):
    """Model for tracking order assignments to riders"""
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted by Rider'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]
    
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='delivery_assignment')
    rider = models.ForeignKey(DeliveryRider, on_delete=models.SET_NULL, null=True, related_name='assignments')
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    delivery_instructions = models.TextField(blank=True, null=True)
    delivery_notes = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['rider', 'status']),
        ]
    
    def __str__(self):
        return f"Assignment: Order #{self.order.order_number} - {self.rider.name if self.rider else 'Unassigned'}"


