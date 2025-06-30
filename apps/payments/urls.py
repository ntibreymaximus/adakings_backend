from django.urls import path
from .views import (
    PaymentListAPIView,
    PaymentDetailAPIView,
    PaymentInitiateAPIView,
    PaystackVerifyAPIView,
    PaystackWebhookAPIView,
    PaymentModesAPIView,
    PaymentTransactionListAPIView,
    TransactionTableAPIView,
    PaymentHistoryAPIView
)

app_name = 'payments_api'

urlpatterns = [
    path('', PaymentListAPIView.as_view(), name='payment-list'),
    path('transactions/', PaymentTransactionListAPIView.as_view(), name='transaction-list'),
    path('transaction-table/', TransactionTableAPIView.as_view(), name='transaction-table'),
    path('payment-history/', PaymentHistoryAPIView.as_view(), name='payment-history'),
    path('initiate/', PaymentInitiateAPIView.as_view(), name='payment-initiate'),
    path('verify/<uuid:reference>/', PaystackVerifyAPIView.as_view(), name='verify-payment'), # Use UUID for our reference
    path('webhook/paystack/', PaystackWebhookAPIView.as_view(), name='paystack-webhook'),
    path('<uuid:reference>/', PaymentDetailAPIView.as_view(), name='payment-detail'), # Detail view by UUID reference
    path('payment-modes/', PaymentModesAPIView.as_view(), name='payment-modes'),
]

