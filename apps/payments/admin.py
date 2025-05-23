from django.contrib import admin
from .models import Payment, PaymentTransaction


class PaymentTransactionInline(admin.StackedInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ['transaction_id', 'status', 'amount', 
                       'created_at']
    can_delete = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'payment_method', 'status', 'amount', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['order__customer_name', 'order__customer_phone', 'reference', 'paystack_reference']
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
        # Prevent deletion of payments to maintain financial records
        return False


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'transaction_id', 'status', 'amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['payment__reference', 'transaction_id', 'payment__order__customer_name']
    readonly_fields = ['payment', 'transaction_id', 'status', 'amount', 
                       'created_at']

