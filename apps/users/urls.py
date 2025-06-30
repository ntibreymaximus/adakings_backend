from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    ProfileUpdateView,
    PasswordResetView,
    PasswordResetConfirmView,
    StaffManagementViewSet,
)

app_name = 'users_api'

router = DefaultRouter()
router.register(r'all', UserViewSet, basename='user') # For admin to see all users
router.register(r'staff', StaffManagementViewSet, basename='staff')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/confirm/<str:uid>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

