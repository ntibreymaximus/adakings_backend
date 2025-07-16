from django.urls import path
from . import views

app_name = 'google_sheets'

urlpatterns = [
    # Google Sheets API endpoints
    path('sheets-url/', views.get_sheets_url, name='sheets-url'),
    path('sync/<str:order_number>/', views.sync_order, name='sync-order'),
    path('bulk-sync/', views.bulk_sync_orders, name='bulk-sync'),
    path('test-connection/', views.test_connection, name='test-connection'),
]
