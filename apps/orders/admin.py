from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Order, OrderItem, OrderItemExtra

# Register your models here.
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'delivery_type', 'location_display', 'created_at')
    list_filter = ('delivery_type', 'created_at')
    search_fields = ('name', 'phone_number', 'location')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'phone_number')
        }),
        ('Delivery Details', {
            'fields': ('delivery_type', 'location')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def location_display(self, obj):
        if obj.delivery_type == 'Pickup':
            return format_html('<span style="color: #999;">Pickup</span>')
        return obj.location
    location_display.short_description = 'Location'


class OrderItemExtraInline(admin.TabularInline):
    model = OrderItemExtra
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('extra', 'quantity', 'unit_price', 'subtotal')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:  # If this is an edit (not an add)
            return self.readonly_fields + ('extra',)
        return self.readonly_fields


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('menu_item', 'quantity', 'unit_price', 'subtotal')
    show_change_link = True
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:  # If this is an edit (not an add)
            return self.readonly_fields + ('menu_item',)
        return self.readonly_fields


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_phone', 'delivery_info', 
                   'formatted_total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'customer__delivery_type')
    search_fields = ('customer__name', 'customer__phone_number', 'customer__location')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
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
        return obj.customer.name
    customer_name.short_description = 'Customer'
    
    def customer_phone(self, obj):
        return obj.customer.phone_number
    customer_phone.short_description = 'Phone'
    
    def delivery_info(self, obj):
        if obj.customer.delivery_type == 'Pickup':
            return format_html('<span style="background-color: #f9f9f9; padding: 2px 6px; border-radius: 3px;">Pickup</span>')
        return format_html('<span style="background-color: #e8f4f8; padding: 2px 6px; border-radius: 3px;">Delivery to: {}</span>', obj.customer.location)
    delivery_info.short_description = 'Delivery Info'
    
    def formatted_total_price(self, obj):
        return format_html('<b>${:.2f}</b>', obj.total_price)
    formatted_total_price.short_description = 'Total'
    
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


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'menu_item_name', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('order__customer__name', 'menu_item__name')
    readonly_fields = ('subtotal',)
    inlines = [OrderItemExtraInline]
    
    def order_id(self, obj):
        return f"Order #{obj.order.id}"
    order_id.short_description = 'Order'
    
    def menu_item_name(self, obj):
        return obj.menu_item.name
    menu_item_name.short_description = 'Menu Item'


# Register the models with their custom admin classes
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(OrderItemExtra)
