from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.menu.models import MenuItem, Extra

# Validator for Ghanaian phone numbers
phone_regex = RegexValidator(
    regex=r"^(\+233|0)\d{9}$",
    message="Phone number must be in format '+233XXXXXXXXX' or '0XXXXXXXXX'."
)

class Order(models.Model):
    """Model for tracking customer orders with customer information"""
    # ... [previous fields remain the same]

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

    # ... [rest of the model remains the same]
