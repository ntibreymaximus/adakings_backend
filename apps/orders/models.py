from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from apps.menu.models import MenuItem

# Validator for Ghanaian phone numbers
phone_regex = RegexValidator(
    regex=r"^(\+233|0)\d{9}$",
    message="Phone number must be in format '+233XXXXXXXXX' or '0XXXXXXXXX'."
)

class Order(models.Model):
    """Model for tracking customer orders with customer information"""
    # Order identification
    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Unique order number in format DDMMYY-XXX"
    )
    
    # Customer information fields
    customer_name = models.CharField(
        max_length=255,
        default="Unknown Customer"
    )
    customer_phone = models.CharField(
        max_length=15,
        validators=[phone_regex],
        help_text="Ghanaian phone number in format +233XXXXXXXXX or 0XXXXXXXXX",
        default="0000000000"
    )
    
    LOCATION_CHOICES = [
        ("Adenta", "Adenta"),
        ("Accra", "Accra"),
        ("Madina", "Madina"),
        ("Legon", "Legon"),
    ]
    DELIVERY_CHOICES = [
        ("Pickup", "Pickup"),
        ("Delivery", "Delivery"),
    ]
    delivery_type = models.CharField(
        max_length=10,
        choices=DELIVERY_CHOICES,
        default="Pickup"
    )
    delivery_location = models.CharField(
        max_length=50,  # Max length for location names
        choices=LOCATION_CHOICES,
        blank=True,     # Still allow blank if delivery_type is not 'Delivery'
        default="Accra", # Or choose another default, or remove if no default preferred
        help_text="Select delivery location (Required for delivery orders)."
    )
    
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Processing", "Processing"),
        ("Ready", "Ready"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def is_paid(self):
        """Check if order has a completed payment"""
        return self.payments.filter(status="completed").exists()

    def get_payment_status(self):
        """Get the payment status with appropriate styling"""
        if self.is_paid():
            return "PAID"
        elif self.payments.filter(status__in=["pending", "processing"]).exists():
            return "PENDING"
        return "UNPAID"
    
    def clean(self):
        # Location is required for delivery orders
        if self.delivery_type == "Delivery" and not self.delivery_location:
            raise ValidationError({"delivery_location": "Location is required for delivery orders."})
        super().clean()
    
    def calculate_total(self):
        """Calculate total price based on all order items"""
        self.total_price = sum(
            item.calculate_subtotal() for item in self.items.all()
        )
        return self.total_price
    
    def generate_order_number(self):
        """Generate a unique order number in the format DDMMYY-XXX"""
        # Get current date in DDMMYY format
        date_part = timezone.now().strftime("%d%m%y")
        
        # Get the latest order with the same date part
        latest_orders = Order.objects.filter(
            order_number__startswith=date_part
        ).order_by('-order_number')
        
        if latest_orders.exists():
            # Extract the numeric part after the hyphen
            latest_number = latest_orders.first().order_number
            try:
                seq_number = int(latest_number.split('-')[1]) + 1
            except (IndexError, ValueError):
                seq_number = 1
        else:
            # No orders for today yet
            seq_number = 1
            
        # Format with leading zeros (e.g., 001, 012, 123)
        return f"{date_part}-{seq_number:03d}"
    
    def save(self, *args, **kwargs):
        print(f"[Order.save] Called for Order PK {self.pk if self.pk else 'NEW'}. Current total_price before any calculation: {getattr(self, 'total_price', 'Not Set')}")
        
        self.full_clean() # Validate fields
        
        if not self.order_number:
            self.order_number = self.generate_order_number()
            print(f"[Order.save] Generated order number: {self.order_number} for PK {self.pk}")
        
        # Calculate total price if order exists (has a PK)
        if self.pk:
            print(f"[Order.save] Calculating total for existing order PK {self.pk}.")
            # Store current total_price before recalculation for comparison
            original_total_on_instance = self.total_price
            
            # calculate_total() updates self.total_price directly and returns it
            recalculated_total = self.calculate_total() 
            
            print(f"[Order.save] Order PK {self.pk}: Instance total_price before calc: {original_total_on_instance}, after calc (self.total_price): {self.total_price}, calculate_total returned: {recalculated_total}")
        else:
            print(f"[Order.save] New order (no PK yet), total price calculation skipped in this block. Current total: {self.total_price}") # Should be default 0.00

        print(f"[Order.save] About to call super().save for Order PK {self.pk if self.pk else 'NEW'}. Total price to be saved: {self.total_price}")
        super().save(*args, **kwargs)
        print(f"[Order.save] super().save completed for Order PK {self.pk}. Final total_price on instance: {self.total_price}")
    
    def __str__(self):
        return f"{self.order_number} - {self.customer_name} ({self.status})"
    
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

class OrderItem(models.Model):
    """Model for individual items within an order"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="order_items"
    )
    parent_item = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, # If parent is deleted, extra is deleted.
        null=True, 
        blank=True, 
        related_name='child_items',
        help_text="Link to the main item if this is an extra."
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        blank=True  # Allow form submission with this field empty
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_subtotal(self):
        """Calculate subtotal based on item price"""
        self.subtotal = self.quantity * self.unit_price
        return self.subtotal
    
    def save(self, *args, **kwargs):
        # Set unit price from menu item if not set
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        
        # Calculate the subtotal
        self.subtotal = self.calculate_subtotal()
        
        # Save the item
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} (Order {self.order.order_number})"
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["created_at"]

