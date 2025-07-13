from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    DeliveryRider, OrderAssignment, DeliveryLocation
)


@admin.register(DeliveryRider)
class DeliveryRiderAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone', 'status', 'current_orders_display', 
        'total_deliveries', 'rating', 'availability_status', 'view_current_orders'
    ]
    list_filter = ['status', 'is_available', 'created_at']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'total_deliveries', 'rating', 'current_assignments_display']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'phone', 'user')
        }),
        ('Status & Availability', {
            'fields': ('status', 'is_available', 'current_orders', 'max_concurrent_orders')
        }),
        ('Performance', {
            'fields': ('total_deliveries', 'rating')
        }),
        ('Current Assignments', {
            'fields': ('current_assignments_display',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_orders_display(self, obj):
        """Display current orders with max limit"""
        return f"{obj.current_orders} / {obj.max_concurrent_orders}"
    current_orders_display.short_description = "Current/Max Orders"
    
    def availability_status(self, obj):
        """Show availability status with color coding"""
        if not obj.is_available:
            return format_html('<span style="color: red;">❌ Manually Unavailable</span>')
        elif obj.current_orders >= obj.max_concurrent_orders:
            return format_html('<span style="color: orange;">⚠️ At Capacity</span>')
        elif obj.status != 'active':
            return format_html('<span style="color: gray;">⏸️ {}</span>', obj.get_status_display())
        else:
            return format_html('<span style="color: green;">✅ Available</span>')
    availability_status.short_description = "Availability"
    
    def view_current_orders(self, obj):
        """Link to view current assignments"""
        count = obj.assignments.filter(
            status__in=['assigned', 'accepted', 'picked_up', 'in_transit']
        ).count()
        if count > 0:
            url = reverse('admin:deliveries_orderassignment_changelist') + f'?rider__id__exact={obj.id}&status__in=assigned,accepted,picked_up,in_transit'
            return format_html('<a href="{}">View {} orders</a>', url, count)
        return "-"
    view_current_orders.short_description = "Current Orders"
    
    def current_assignments_display(self, obj):
        """Display current assignments in detail view"""
        assignments = obj.assignments.filter(
            status__in=['assigned', 'accepted', 'picked_up', 'in_transit']
        ).select_related('order')
        
        if not assignments:
            return "No current assignments"
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background-color: #f0f0f0;">'
        html += '<th style="padding: 8px; text-align: left;">Order #</th>'
        html += '<th style="padding: 8px; text-align: left;">Status</th>'
        html += '<th style="padding: 8px; text-align: left;">Customer</th>'
        html += '<th style="padding: 8px; text-align: left;">Delivery Location</th>'
        html += '<th style="padding: 8px; text-align: left;">Actions</th>'
        html += '</tr>'
        
        for assignment in assignments:
            order = assignment.order
            url = reverse('admin:deliveries_orderassignment_change', args=[assignment.id])
            html += '<tr style="border-bottom: 1px solid #ddd;">'
            html += f'<td style="padding: 8px;">{order.order_number}</td>'
            html += f'<td style="padding: 8px;">{assignment.get_status_display()}</td>'
            html += f'<td style="padding: 8px;">{order.user.get_full_name() or order.user.email}</td>'
            html += f'<td style="padding: 8px;">{order.delivery_location or "N/A"}</td>'
            html += f'<td style="padding: 8px;"><a href="{url}">View Details</a></td>'
            html += '</tr>'
        
        html += '</table>'
        return format_html(html)
    current_assignments_display.short_description = "Current Assignments"


@admin.register(OrderAssignment)
class OrderAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'rider_name', 'status', 'picked_up_at', 'delivered_at'
    ]
    list_filter = ['status', 'rider']
    search_fields = ['order__order_number', 'rider__name']
    readonly_fields = [
        'picked_up_at', 'delivered_at'
    ]
    raw_id_fields = ['order', 'rider']
    list_editable = ['status']  # Allow status editing from list view
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order Number'
    
    def rider_name(self, obj):
        return obj.rider.name if obj.rider else 'Unassigned'
    rider_name.short_description = 'Rider'
    
    fieldsets = (
        ('Order & Rider', {
            'fields': ('order', 'rider', 'status')
        }),
        ('Delivery Details', {
            'fields': (
                'delivery_instructions', 'delivery_notes'
            )
        }),
        ('Timestamps', {
            'fields': (
                'picked_up_at', 'delivered_at'
            ),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeliveryLocation)
class DeliveryLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'fee', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


