from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.menu.models import MenuItem, Extra


# Validator for Ghanaian phone numbers
phone_regex = RegexValidator(
    regex=r'^(\+233|0)\d{9}$',
    message="Phone number must be in format '+233XXXXXXXXX' or '0XXXXXXXXX'."
)


class Customer(models.Model):
    """Model for storing customer information for orders"""
    name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15,
        validators=[phone_regex],
        help_text="Ghanaian phone number in format +233XXXXXXXXX or 0XXXXXXXXX"
    )
    DELIVERY_CHOICES = [
        ('Pickup', 'Pickup'),
        ('Delivery', 'Delivery'),
    ]
    delivery_type = models.CharField(
        max_length=10,
        choices=DELIVERY_CHOICES,
        default='Pickup'
    )
    location = models.TextField(
        blank=True,
        help_text="Required for delivery orders, leave blank for pickup"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

    def clean(self):
        # Location is required for delivery orders
        if self.delivery_type == 'Delivery' and not self.location:
            raise ValidationError({'location': 'Location is required for delivery orders.'})
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Order(models.Model):
    """Model for tracking customer orders"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Processing', 'Processing'),
        ('Ready', 'Ready'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name} ({self.status})"

    def get_formatted_total_price(self):
        return f"${self.total_price:.2f}"

    def calculate_total(self):
        """Calculate total price based on all order items and their extras"""
        self.total_price = sum(
            item.subtotal for item in self.items.all()
        )
        return self.total_price

    def save(self, *args, **kwargs):
        # First save to get an ID if this is a new order
        super().save(*args, **kwargs)
        # Calculate the total price and save again
        self.total_price = self.calculate_total()
        # Avoid potential recursion by using update instead of save
        if self.pk:
            Order.objects.filter(pk=self.pk).update(total_price=self.total_price)


class OrderItem(models.Model):
    """Model for individual menu items in an order"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    def get_formatted_subtotal(self):
        return f"${self.subtotal:.2f}"

    def calculate_subtotal(self):
        """Calculate subtotal for this item including any extras"""
        item_subtotal = self.quantity * self.unit_price
        extras_subtotal = sum(
            extra.subtotal for extra in self.extras.all()
        )
        return item_subtotal + extras_subtotal

    def save(self, *args, **kwargs):
        # If new item, set unit_price from menu_item
        if not self.unit_price:
            self.unit_price = self.menu_item.price

        # First save to establish relationship with extras if needed
        super().save(*args, **kwargs)
        
        # Calculate subtotal and save again
        self.subtotal = self.calculate_subtotal()
        
        # Avoid potential recursion by using update instead of save
        if self.pk:
            OrderItem.objects.filter(pk=self.pk).update(subtotal=self.subtotal)
            # Update the parent order's total
            self.order.save()


class OrderItemExtra(models.Model):
    """Model for extras associated with order items"""
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='extras'
    )
    extra = models.ForeignKey(
        Extra,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    class Meta:
        verbose_name = 'Order Item Extra'
        verbose_name_plural = 'Order Item Extras'
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.extra.name} for {self.order_item}"

    def get_formatted_subtotal(self):
        return f"${self.subtotal:.2f}"

    def calculate_subtotal(self):
        """Calculate subtotal for this extra"""
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        # If new item, set unit_price from extra
        if not self.unit_price:
            self.unit_price = self.extra.price
            
        # Calculate subtotal
        self.subtotal = self.calculate_subtotal()
        
        super().save(*args, **kwargs)
        
        # Update the parent order item's subtotal
        if self.order_item:
            self.order_item.save()

from django.db import models

# Create your models here.
