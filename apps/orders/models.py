from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from apps.menu.models import MenuItem

DELIVERY_FEES = {
    "Adenta": Decimal("5.00"),
    "Accra": Decimal("7.00"),
    "Madina": Decimal("4.00"),
    "Legon": Decimal("3.00"),
    # Ensure all LOCATION_CHOICES used for 'Delivery' are mapped here
}

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
    
    # Dynamically create LOCATION_CHOICES from DELIVERY_FEES dictionary
    # This ensures that the dropdown options for delivery_location show the fee.
    LOCATION_CHOICES = [
        (location, f"{location} (Fee: ₵{fee:.2f})")
        for location, fee in DELIVERY_FEES.items()
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
        ("Accepted", "Accepted"),
        ("Ready", "Ready"),
        ("Out for Delivery", "Out for Delivery"),
        ("Fulfilled", "Fulfilled"),
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
    delivery_fee = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00"),
        help_text="Calculated delivery fee for the order"
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def amount_paid(self):
        """Calculates the total amount paid from 'completed' payments, net of refunds."""
        # self.payments.model refers to the Payment model
        completed_payments = self.payments.filter(status=self.payments.model.STATUS_COMPLETED, payment_type=self.payments.model.PAYMENT_TYPE_PAYMENT)
        total_paid_val = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        completed_refunds = self.payments.filter(status=self.payments.model.STATUS_COMPLETED, payment_type=self.payments.model.PAYMENT_TYPE_REFUND)
        total_refunded_val = completed_refunds.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return total_paid_val - total_refunded_val

    def balance_due(self):
        """Calculates the outstanding balance for the order."""
        balance = self.total_price - self.amount_paid()
        # If balance is negative (overpayment), balance_due is 0. amount_overpaid handles the negative part.
        return max(balance, Decimal('0.00'))

    def amount_overpaid(self):
        """Calculates the amount overpaid by the customer."""
        overpaid = self.amount_paid() - self.total_price
        return max(overpaid, Decimal('0.00'))

    def is_paid(self):
        """Check if order's balance due is zero (i.e., fully paid or overpaid)."""
        # An order is considered paid if the balance due is 0.
        # This means total_price <= amount_paid_net_of_refunds
        return self.balance_due() == Decimal('0.00')

    def get_payment_status(self):
        """Get the payment status: UNPAID, PARTIALLY PAID, PAID, OVERPAID, PENDING PAYMENT."""
        paid_amount_net = self.amount_paid()

        if paid_amount_net < self.total_price:
            if paid_amount_net > Decimal('0.00'):
                return "PARTIALLY PAID"
            else: # paid_amount_net is 0.00 or less
                # Check for any non-completed 'payment' type transactions
                if self.payments.filter(
                    payment_type=self.payments.model.PAYMENT_TYPE_PAYMENT, 
                    status__in=[self.payments.model.STATUS_PENDING, self.payments.model.STATUS_PROCESSING]
                ).exists():
                    return "PENDING PAYMENT"
                return "UNPAID"
        elif paid_amount_net == self.total_price:
            return "PAID"
        else: # paid_amount_net > self.total_price
            return "OVERPAID"
    
    def clean(self):
        # Location is required for delivery orders
        if self.delivery_type == "Delivery":
            if not self.delivery_location:
                raise ValidationError({"delivery_location": "Location is required for delivery orders."})
            # New check for fee existence
            if self.delivery_location not in DELIVERY_FEES:
                raise ValidationError({"delivery_location": f"Delivery to '{self.delivery_location}' is not currently supported or has no defined fee."})
        super().clean()
    
    def _calculate_delivery_fee(self):
        if self.delivery_type == "Pickup":
            return Decimal("0.00")
        elif self.delivery_type == "Delivery":
            if self.delivery_location and self.delivery_location in DELIVERY_FEES:
                return DELIVERY_FEES.get(self.delivery_location, Decimal("0.00"))
            else:
                # This case should ideally be caught by clean() method if location is invalid
                return Decimal("0.00") 
        return Decimal("0.00")

    def calculate_total(self):
        """Calculate total price based on all order items and delivery fee"""
        sum_of_items = Decimal("0.00") # Initialize to Decimal
        if self.pk: # Check if the order instance has a primary key
            # If it has a PK, it's an existing order, so we can access related items
            sum_of_items = sum(
                item.calculate_subtotal() for item in self.items.all()
            )
        # Ensure delivery_fee is a Decimal for calculation
        calculated_delivery_fee = self.delivery_fee if self.delivery_fee is not None else Decimal("0.00")
        self.total_price = sum_of_items + calculated_delivery_fee
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
        self.full_clean() # Validate fields
        
        # Calculate and set delivery fee
        self.delivery_fee = self._calculate_delivery_fee()

        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Calculate total price (this will use the self.delivery_fee set above)
        # This needs to happen for both new and existing orders if items might be involved or delivery fee changed.
        # For new orders, items are usually added after the initial Order instance is saved,
        # so calculate_total() is often called again after items are linked.
        # For existing orders, this ensures total_price is up-to-date.
        
        # Let's ensure calculate_total is called consistently. 
        # If it's a new order, items aren't linked yet, so sum_of_items will be 0.
        # total_price will be just delivery_fee. This is fine as it will be recalculated
        # in the view after items are added.
        self.calculate_total() # This updates self.total_price

        super().save(*args, **kwargs)
    
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
        # Decimal('0.00') or None should trigger this. In Python, Decimal(0) is falsy.
        if not self.unit_price or self.unit_price == Decimal('0.00'): 
            if self.menu_item and hasattr(self.menu_item, 'price') and self.menu_item.price is not None:
                self.unit_price = self.menu_item.price
        
        # Ensure quantity is a number, default to 1 if None for calculation safety
        current_quantity = self.quantity if self.quantity is not None else 1
        current_unit_price = self.unit_price if self.unit_price is not None else Decimal('0.00')

        # Calculate the subtotal (ensure types are compatible for multiplication)
        self.subtotal = Decimal(current_quantity) * Decimal(current_unit_price)
        # self.subtotal = self.calculate_subtotal() # calculate_subtotal() might be better if it handles None robustly
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} (Order {self.order.order_number})"
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["created_at"]

