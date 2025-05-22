from django.urls import path


from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Staff management (admin only)
    path('staff/register/', views.StaffRegistrationView.as_view(), name='staff_register'),
    path('staff/list/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    
    # User profile
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    
    # Dashboard redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Role-specific dashboards
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('dashboard/frontdesk/', views.FrontdeskDashboardView.as_view(), name='frontdesk_dashboard'),
    path('dashboard/kitchen/', views.KitchenDashboardView.as_view(), name='kitchen_dashboard'),
    path('dashboard/delivery/', views.DeliveryDashboardView.as_view(), name='delivery_dashboard'),
    
    # Access denied
    path('access-denied/', views.AccessDeniedView.as_view(), name='access_denied'),
    
    # Password reset
    path('password-reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),
    path('password-reset/done/', 
         views.CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('password-reset/complete/', 
         views.CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
]

