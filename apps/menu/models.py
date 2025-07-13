from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class MenuItem(models.Model):
    """Model for all menu items, including both regular items and extras"""
    
    ITEM_TYPES = [
        ('regular', 'Regular Item'),
        ('extra', 'Extra Item'),
        ('bolt', 'Bolt Item'),
        ('wix', 'WIX Item'),
    ]
    
    name = models.CharField(max_length=200, unique=True, db_index=True)  # Index for fast name lookups
    item_type = models.CharField(
        max_length=10,
        choices=ITEM_TYPES,
        default='regular',
        help_text='Type of menu item: regular, extra, bolt, or wix',
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
        type_display = {
            'regular': 'Regular',
            'extra': 'Extra',
            'bolt': 'Bolt',
            'wix': 'WIX'
        }
        return f"{self.name} ({type_display.get(self.item_type, self.item_type)})"

    def get_formatted_price(self):
        return f"₵{self.price:.2f}"

    def get_usage_count(self):
        """Get the number of times this item is used in orders"""
        return self.order_items.count()

    @property
    def is_extra(self):
        """Helper method to check if this is an extra item"""
        return self.item_type == 'extra'
    
    @property
    def is_bolt(self):
        """Helper method to check if this is a Bolt item"""
        return self.item_type == 'bolt'
    
    @property
    def is_wix(self):
        """Helper method to check if this is a WIX item"""
        return self.item_type == 'wix'
