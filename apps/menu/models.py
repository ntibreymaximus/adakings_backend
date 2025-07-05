from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class MenuItem(models.Model):
    """Model for all menu items, including both regular items and extras"""
    
    ITEM_TYPES = [
        ('regular', 'Regular Item'),
        ('extra', 'Extra Item'),
    ]
    
    name = models.CharField(max_length=200, unique=True, db_index=True)  # Index for fast name lookups
    item_type = models.CharField(
        max_length=10,
        choices=ITEM_TYPES,
        default='regular',
        help_text='Whether this is a regular menu item or an extra',
        db_index=True  # Index for fast filtering by type
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_available = models.BooleanField(default=True, db_index=True)  # Index for fast availability filtering
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_menu_items'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for ordering
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        ordering = ['item_type', 'name']
        # Compound indexes for common query patterns
        indexes = [
            models.Index(fields=['item_type', 'is_available'], name='menu_type_available_idx'),
            models.Index(fields=['is_available', 'item_type', 'name'], name='menu_available_type_name_idx'),
            models.Index(fields=['created_at', 'item_type'], name='menu_created_type_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({'Extra' if self.item_type == 'extra' else 'Regular'})"

    def get_formatted_price(self):
        return f"₵{self.price:.2f}"

    def get_usage_count(self):
        """Get the number of times this item is used in orders"""
        return self.order_items.count()

    @property
    def is_extra(self):
        """Helper method to check if this is an extra item"""
        return self.item_type == 'extra'
