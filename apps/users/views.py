from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from .models import User
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm,
    CustomAuthenticationForm, CustomPasswordResetForm,
    CustomSetPasswordForm
)
from apps.orders.models import Order

def admin_required(function):
    """Decorator for views that checks that the user is admin."""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_admin,
        login_url='users:access_denied'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def frontdesk_required(function):
    """Decorator for views that checks that the user is frontdesk staff."""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_frontdesk or u.is_admin),
        login_url='users:access_denied'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'users:login'

@login_required
def dashboard_redirect(request):
    """Redirect users to their role-specific dashboard."""
    if request.user.is_admin:
        return redirect('users:admin_dashboard')
    elif request.user.is_frontdesk:
        return redirect('users:frontdesk_dashboard')
    elif request.user.is_kitchen:
        return redirect('users:kitchen_dashboard')
    elif request.user.is_delivery:
        return redirect('users:delivery_dashboard')
    return redirect('users:access_denied')

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/dashboards/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your admin dashboard context here
        return context

class FrontdeskDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboards/frontdesk_dashboard.html'

    @method_decorator(frontdesk_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get today's date
        today = timezone.now().date()
        
        # Get recent orders (last 24 hours)
        recent_orders = Order.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).order_by('-created_at')[:10]

        # Get today's stats
        today_orders = Order.objects.filter(
            created_at__date=today
        )
        
        # Calculate total amount with proper handling for empty queryset
        total_amount = today_orders.aggregate(
            total=Sum('total_price')
        )['total'] or 0.00
        
        context.update({
            'recent_orders': recent_orders,
            'today_stats': {
                'total_orders': today_orders.count(),
                'total_amount': total_amount,
                'pending_orders': today_orders.filter(status='Pending').count(),
                'completed_orders': today_orders.filter(
                    status__in=['Delivered', 'Ready']
                ).count(),
            }
        })
        
        return context

class KitchenDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/dashboards/kitchen_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_kitchen
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your kitchen dashboard context here
        return context

class DeliveryDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/dashboards/delivery_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_delivery
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your delivery dashboard context here
        return context

class AccessDeniedView(TemplateView):
    template_name = 'users/access_denied.html'

class StaffRegistrationView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/staff_form.html'
    success_url = reverse_lazy('users:staff_list')
    success_message = "Staff member was created successfully"
    
    def test_func(self):
        return self.request.user.is_admin

class StaffListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users/staff_list.html'
    context_object_name = 'staff_members'
    
    def test_func(self):
        return self.request.user.is_admin
    
    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk)

class StaffDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'users/staff_detail.html'
    context_object_name = 'staff_member'
    
    def test_func(self):
        return self.request.user.is_admin

class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('users:profile')
    success_message = "Your profile was updated successfully"
    
    def get_object(self):
        return self.request.user

class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('users:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'
