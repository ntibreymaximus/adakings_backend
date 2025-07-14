from django.contrib import admin
from django.contrib import messages
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.http import HttpResponseRedirect
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('menu_item', 'quantity', 'unit_price', 'subtotal', 'notes')
    readonly_fields = ('subtotal', 'unit_price')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Sorts items to show 'regular' items before 'extra' items.
        return qs.select_related('menu_item').order_by('-menu_item__item_type', 'menu_item__name')
    
    def has_delete_permission(self, request, obj=None):
        return True

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_phone', 'delivery_info', 
                   'total_price_display', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'delivery_type')
    search_fields = ('customer_phone', 'delivery_location__name')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_phone',)
        }),
        ('Delivery Details', {
            'fields': ('delivery_type', 'delivery_location')
        }),
        ('Order Details', {
            'fields': ('status', 'total_price', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_ready', 'mark_as_delivered', 'mark_as_cancelled']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            calculated_total=Coalesce(Sum('items__subtotal'), Value(0), output_field=DecimalField()) + F('delivery_fee')
        )
        return queryset

    def save_formset(self, request, form, formset, change):
        # First, let the default behavior save the inline formset (OrderItems)
        super().save_formset(request, form, formset, change)
        
        # 'form.instance' is the parent Order object.
        order_instance = form.instance
        
        if order_instance and order_instance.pk:
            new_total_price = order_instance.calculate_total()
            
            # Get the current total_price from the instance. This might have been affected by super().save_formset or signals.
            current_total_price_in_instance = order_instance.total_price
            
            if current_total_price_in_instance != new_total_price or new_total_price is not None: # Try to save if different, or if new_total_price is a valid number (even if 0)
                order_instance.total_price = new_total_price
                try:
                    order_instance.save(update_fields=['total_price'])
                    # Re-fetch from DB to confirm persisted value if needed for further logic, otherwise optional
                    # refreshed_order = type(order_instance).objects.get(pk=order_instance.pk)
                except Exception as e:
                    # Consider logging this error instead of a user-facing message if it's unexpected
                    messages.error(request, f"An error occurred while updating order total: {e}")
        # elif not order_instance:
            # This case should ideally not happen if the main form is valid
            # messages.warning(request, "DEBUG: save_formset - order_instance (form.instance) is None.")
        # elif not order_instance.pk:
            # This case implies the main order object wasn't saved before formset, which Django handles
            # messages.warning(request, f"DEBUG: save_formset - order_instance {order_instance} has no PK yet.")

    def customer_phone(self, obj):
        return obj.customer_phone
    customer_phone.short_description = 'Phone'
    
    def delivery_info(self, obj):
        if obj.delivery_type == 'Pickup':
            return 'Pickup'
        elif obj.delivery_type == 'Delivery':
            # Use historical name if available
            location_name = obj.get_effective_delivery_location_name()
            if location_name:
                return f'Delivery to: {location_name}'
            return 'Delivery (No location set)'
        return 'N/A'
    delivery_info.short_description = 'Delivery Info'
    
    def total_price_display(self, obj):
        return f"₵{obj.calculated_total:.2f}"
    total_price_display.admin_order_field = 'calculated_total'
    total_price_display.short_description = 'Total Price'
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='Confirmed')
    mark_as_confirmed.short_description = "Mark selected orders as confirmed"
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='Processing')
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    def mark_as_ready(self, request, queryset):
        queryset.update(status='Ready')
    mark_as_ready.short_description = "Mark selected orders as ready"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='Delivered')
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='Cancelled')
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"
    
    def has_related_payments(self, obj):
        """Check if the order has any related payments."""
        if obj:
            return obj.payments.filter(status='completed').exists()
        return False

    def has_delete_permission(self, request, obj=None):
        """Superadmins can delete anything, others cannot delete orders with payments."""
        # Superadmins have unrestricted access
        if (request.user.is_superuser and 
            hasattr(request.user, 'role') and 
            request.user.role == 'superadmin'):
            return True
            
        # For other users, prevent deletion of orders with related payments
        if obj and self.has_related_payments(obj):
            return False
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        """Show warning message if deletion is attempted on orders with payments (except for superadmins)."""
        obj = self.get_object(request, object_id)
        
        # Superadmins can delete anything without restrictions
        if (request.user.is_superuser and 
            hasattr(request.user, 'role') and 
            request.user.role == 'superadmin'):
            return super().delete_view(request, object_id, extra_context)
        
        # For other users, check payment restrictions
        if obj and self.has_related_payments(obj):
            self.message_user(
                request, 
                f"Order {obj.order_number} cannot be deleted because it has associated payments.",
                level=messages.ERROR
            )
            return HttpResponseRedirect(
                reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), 
                        args=[object_id])
            )
        return super().delete_view(request, object_id, extra_context)

    def get_deleted_objects(self, objs, request):
        """Customize the deletion information to inform about related payments."""
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        
        # Check if any of the objects have payments and add an informative message
        for obj in objs:
            if self.has_related_payments(obj):
                perms_needed.add(f"Order {obj.order_number} has completed payments and cannot be deleted")
        
        return deleted_objects, model_count, perms_needed, protected

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'menu_item_name', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('order__customer_phone', 'menu_item__name')
    readonly_fields = ('subtotal',)
    
    def order_id(self, obj):
        return obj.order.order_number
    order_id.short_description = 'Order'
    
    def menu_item_name(self, obj):
        return obj.menu_item.name
    menu_item_name.short_description = 'Menu Item'
