from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment selection and processing
    path('process/<int:order_id>/', views.PaymentMethodSelectionView.as_view(), name='process_payment'),
    
    # Cash payment processing
    path('cash/<int:payment_id>/', views.CashPaymentView.as_view(), name='cash_payment'),
    
    # Mobile money payment processing
    path('mobile/<int:payment_id>/', views.MobilePaymentView.as_view(), name='mobile_payment'),
    
    # Payment verification
    path('verify/<str:reference>/', views.VerifyPaymentView.as_view(), name='verify_payment'),
    
    # Paystack webhook
    path('paystack/webhook/', views.PaystackWebhookView.as_view(), name='paystack_webhook'),
    
    # Transaction views
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    
    # Success and failure pages
    path('success/', TemplateView.as_view(template_name='payments/payment_success.html'), name='payment_success'),
    path('failed/', TemplateView.as_view(template_name='payments/payment_failed.html'), name='payment_failed'),
]
