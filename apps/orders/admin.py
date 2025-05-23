from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from .models import Order, OrderItem, OrderItemExtra

class OrderItemExtraInline(admin.TabularInline):
    model = OrderItemExtra
    extra = 0
    fields = ('extra', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)
    
    def has_delete_permission(self, request, obj=None):
        return True

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('menu_item', 'quantity', 'unit_price', 'subtotal', 'notes')
    readonly_fields = ('subtotal',)
    inlines = [OrderItemExtraInline]
    
    def has_delete_permission(self, request, obj=None):
        return True

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_phone', 'delivery_info', 
                   'formatted_total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'delivery_type')
    search_fields = ('customer_name', 'customer_phone', 'delivery_location')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone')
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
    
    def customer_name(self, obj):
        return obj.customer_name
    customer_name.short_description = 'Customer'
    
    def customer_phone(self, obj):
        return obj.customer_phone
    customer_phone.short_description = 'Phone'
    
    def delivery_info(self, obj):
        if obj.delivery_type == 'Pickup':
            return format_html('<span style="background-color: #f9f9f9; padding: 2px 6px; border-radius: 3px;">Pickup</span>')
        return format_html('<span style="background-color: #e8f4f8; padding: 2px 6px; border-radius: 3px;">Delivery to: {}</span>', obj.delivery_location)
    delivery_info.short_description = 'Delivery Info'
    
    def formatted_total_price(self, obj):
        return format_html('${:.2f}', float(obj.total_price))
    formatted_total_price.short_description = 'Total Price'
    
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

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'menu_item_name', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('order__customer_name', 'menu_item__name')
    readonly_fields = ('subtotal',)
    inlines = [OrderItemExtraInline]
    
    def order_id(self, obj):
        return f"#{obj.order.id}"
    order_id.short_description = 'Order'
    
    def menu_item_name(self, obj):
        return obj.menu_item.name
    menu_item_name.short_description = 'Menu Item'

admin.site.register(OrderItemExtra)
