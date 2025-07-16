from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Payment, PaymentTransaction


class PaymentTransactionInline(admin.StackedInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ['transaction_id', 'status', 'amount', 
                       'created_at']
    can_delete = False


class PaymentResource(resources.ModelResource):
    """Resource class for importing/exporting Payments"""
    class Meta:
        model = Payment
        fields = ('id', 'order', 'payment_method', 'status', 'amount', 'reference', 
                 'paystack_reference', 'mobile_number', 'notes', 'created_at', 'updated_at')
        export_order = ('id', 'order', 'payment_method', 'status', 'amount', 'reference', 'created_at')
        import_id_fields = ('reference',)
        skip_unchanged = True
        report_skipped = True

@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    resource_class = PaymentResource
    list_display = ['id', 'order', 'payment_method', 'status', 'amount', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['order__customer_phone', 'reference', 'paystack_reference']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [PaymentTransactionInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order',)
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'status', 'amount', 'reference')
        }),
        ('Paystack Information', {
            'fields': ('paystack_reference', 'mobile_number', 'response_data'),
            'classes': ('collapse',),
        }),
        ('Additional Information', {
            'fields': ('notes', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Only allow superadmins to delete payment records
        # Superadmins have unrestricted access to everything
        return (request.user.is_superuser and 
                hasattr(request.user, 'role') and 
                request.user.role == 'superadmin')
    
    def changelist_view(self, request, extra_context=None):
        """Add informational message about deletion permissions."""
        extra_context = extra_context or {}
        
        if not (request.user.is_superuser and hasattr(request.user, 'role') and request.user.role == 'superadmin'):
            from django.contrib import messages
            messages.info(
                request, 
                "Payment transactions can only be deleted by superadmins. "
                "This ensures financial audit compliance and data integrity."
            )
        
        return super().changelist_view(request, extra_context)


class PaymentTransactionResource(resources.ModelResource):
    """Resource class for importing/exporting Payment Transactions"""
    class Meta:
        model = PaymentTransaction
        fields = ('id', 'payment', 'transaction_id', 'status', 'amount', 'created_at')
        export_order = ('id', 'payment', 'transaction_id', 'status', 'amount', 'created_at')
        import_id_fields = ('transaction_id',)
        skip_unchanged = True
        report_skipped = True

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ImportExportModelAdmin):
    resource_class = PaymentTransactionResource
    list_display = ['id', 'payment', 'transaction_id', 'status', 'amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['payment__reference', 'transaction_id', 'payment__order__customer_phone']
    readonly_fields = ['payment', 'transaction_id', 'status', 'amount', 
                       'created_at']
    
    def has_delete_permission(self, request, obj=None):
        # Only allow superadmins to delete payment transaction records
        # Superadmins have unrestricted access to everything
        return (request.user.is_superuser and 
                hasattr(request.user, 'role') and 
                request.user.role == 'superadmin')
    
    def changelist_view(self, request, extra_context=None):
        """Add informational message about deletion permissions."""
        extra_context = extra_context or {}
        
        if not (request.user.is_superuser and hasattr(request.user, 'role') and request.user.role == 'superadmin'):
            from django.contrib import messages
            messages.info(
                request, 
                "Payment transaction records can only be deleted by superadmins. "
                "This ensures financial audit compliance and data integrity."
            )
        
        return super().changelist_view(request, extra_context)

