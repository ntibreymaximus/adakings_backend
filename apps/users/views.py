from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, 
    PasswordResetDoneView, PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, TemplateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.http import HttpResponseRedirect
from django.db.models import Count
from django.views.decorators.http import require_http_methods

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .decorators import admin_required, frontdesk_required, kitchen_required, delivery_required, role_required_class

# Custom login view with role-based redirects
class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    
    def get_success_url(self):
        """Redirect to different URLs depending on user role"""
        user = self.request.user
        
        # Role-specific redirects
        if user.is_admin():
            return reverse_lazy('users:admin_dashboard')
        elif user.is_frontdesk():
            return reverse_lazy('users:frontdesk_dashboard')
        elif user.is_kitchen():
            return reverse_lazy('users:kitchen_dashboard')
        elif user.is_delivery():
            return reverse_lazy('users:delivery_dashboard')
        else:
            return reverse_lazy('home')  # Fallback
    
    def form_valid(self, form):
        """Add success message on login"""
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome, {self.request.user.get_full_name() or self.request.user.username}!")
        return response


# Staff registration view (admin only)
@method_decorator(admin_required, name='dispatch')
class StaffRegistrationView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:staff_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f"Staff account for {form.cleaned_data['username']} created successfully!"
        )
        return response


# Profile update view
@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your profile has been updated successfully!")
        return response


# Staff list view (admin only)
@method_decorator(admin_required, name='dispatch')
class StaffListView(ListView):
    model = CustomUser
    template_name = 'users/staff_list.html'
    context_object_name = 'staff_list'
    paginate_by = 10  # Show 10 staff members per page
    ordering = ['role', 'username']  # Default ordering


# Staff detail view (admin only)
@method_decorator(admin_required, name='dispatch')
class StaffDetailView(UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/staff_detail.html'
    success_url = reverse_lazy('users:staff_list')
    
    def post(self, request, *args, **kwargs):
        if request.POST.get('_method') == 'DELETE':
            # Handle deletion
            self.object = self.get_object()
            if self.object.is_superuser:
                messages.error(request, "Cannot delete superuser account.")
                return HttpResponseRedirect(self.get_success_url())
            
            username = self.object.username
            self.object.delete()
            messages.success(request, f"Staff account for {username} has been deleted successfully.")
            return HttpResponseRedirect(self.get_success_url())
            
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Staff account for {self.object.username} updated successfully!")
        return response


# Access denied view
class AccessDeniedView(TemplateView):
    template_name = 'users/access_denied.html'


# Password reset views (using Django's built-in views)
class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


# Custom logout view that accepts both GET and POST methods
class CustomLogoutView(LogoutView):
    """
    Custom logout view that allows logout via both GET and POST methods.
    This is useful during development and provides a better user experience.
    """
    next_page = reverse_lazy('users:login')
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle both GET and POST methods for logout"""
        if request.method == 'GET':
            # For GET requests, perform the logout action as if it was a POST
            return self.post(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Add a success message after logout"""
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been successfully logged out.")
        return response


# Role-specific dashboard redirects
@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user role"""
    user = request.user
    
    if user.is_admin():
        return redirect('users:admin_dashboard')
    elif user.is_frontdesk():
        return redirect('users:frontdesk_dashboard')
    elif user.is_kitchen():
        return redirect('users:kitchen_dashboard')
    elif user.is_delivery():
        return redirect('users:delivery_dashboard')
    else:
        messages.warning(request, "Your account doesn't have an assigned role. Please contact an administrator.")
        return redirect('home')


# Dashboard Views
@method_decorator(admin_required, name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'users/dashboards/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add admin-specific context
        total_staff = CustomUser.objects.count()
        context['total_staff'] = total_staff
        
        # Individual role counts
        admin_count = CustomUser.objects.filter(role='admin').count()
        frontdesk_count = CustomUser.objects.filter(role='frontdesk').count()
        kitchen_count = CustomUser.objects.filter(role='kitchen').count()
        delivery_count = CustomUser.objects.filter(role='delivery').count()
        
        context['admin_count'] = admin_count
        context['frontdesk_count'] = frontdesk_count
        context['kitchen_count'] = kitchen_count
        context['delivery_count'] = delivery_count
        
        # Calculate percentages and format them as strings
        if total_staff > 0:
            context['admin_percentage'] = f"{round((admin_count / total_staff) * 100, 1)}"
            context['frontdesk_percentage'] = f"{round((frontdesk_count / total_staff) * 100, 1)}"
            context['kitchen_percentage'] = f"{round((kitchen_count / total_staff) * 100, 1)}"
            context['delivery_percentage'] = f"{round((delivery_count / total_staff) * 100, 1)}"
        else:
            # If there are no staff members, set all percentages to 0
            context['admin_percentage'] = "0"
            context['frontdesk_percentage'] = "0"
            context['kitchen_percentage'] = "0"
            context['delivery_percentage'] = "0"
        
        # Add recent users
        context['recent_users'] = CustomUser.objects.order_by('-date_joined')[:5]
        return context


@method_decorator(frontdesk_required, name='dispatch')
class FrontdeskDashboardView(TemplateView):
    template_name = 'users/dashboards/frontdesk_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add frontdesk-specific context here when you have models for orders, tables, etc.
        return context


@method_decorator(kitchen_required, name='dispatch')
class KitchenDashboardView(TemplateView):
    template_name = 'users/dashboards/kitchen_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add kitchen-specific context here when you have models for food items, orders, etc.
        return context


@method_decorator(delivery_required, name='dispatch')
class DeliveryDashboardView(TemplateView):
    template_name = 'users/dashboards/delivery_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add delivery-specific context here when you have models for deliveries, etc.
        context['delivery_zone'] = self.request.user.delivery_zone
        context['vehicle_type'] = self.request.user.vehicle_type
        return context
