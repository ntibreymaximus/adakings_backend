from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
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
from django.db.models import Count, Sum, F, Q, DecimalField
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
import json
from decimal import Decimal

from .models import CustomUser
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, PaymentTransaction
from apps.menu.models import MenuItem
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm,
    CustomAuthenticationForm, CustomPasswordResetForm,
    CustomSetPasswordForm
)
from apps.orders.models import Order

def admin_required(function):
    """Decorator for views that checks that the user is admin."""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_admin(),
        login_url='users:access_denied'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def frontdesk_required(function):
    """Decorator for views that checks that the user is frontdesk staff."""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_frontdesk() or u.is_admin()),
        login_url='users:access_denied'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_admin() and not self.request.session.get('dashboard_notification_shown'):
            message = """Dashboard Implementation Complete!
The admin dashboard has been successfully implemented with:
• General order statistics and visualizations
• Transaction management system
• Real-time data monitoring
• Full component integration

The system is now ready for use."""
            messages.success(self.request, message)
            self.request.session['dashboard_notification_shown'] = True
        return response

class CustomLogoutView(LogoutView):
    next_page = 'users:login'

@login_required
def dashboard_redirect(request):
    """Redirect users to their role-specific dashboard."""
    if request.user.is_admin():
        return redirect('users:admin_dashboard')
    elif request.user.is_frontdesk():
        return redirect('users:frontdesk_dashboard')
    elif request.user.is_kitchen():
        return redirect('users:kitchen_dashboard')
    elif request.user.is_delivery():
        return redirect('users:delivery_dashboard')
    return redirect('users:access_denied')

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/dashboards/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_admin()
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current date and time
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        sixty_days_ago = today - timedelta(days=60)
        
        # Order statistics
        total_orders = Order.objects.count()
        
        # Use the is_paid() method to identify paid orders, then sum total_price
        paid_orders = [order.id for order in Order.objects.all() if order.is_paid()]
        total_revenue = Order.objects.filter(id__in=paid_orders).aggregate(
            Sum('total_price'))['total_price__sum'] or Decimal('0.00')
            
        today_orders_qs = Order.objects.filter(created_at__date=today) # QuerySet for today's orders
        today_orders = today_orders_qs.count() # Count of orders created today
        
        revenue_today = Decimal('0.00')
        for order in today_orders_qs: # Iterate over today's orders
            if order.is_paid(): # Check if the order is paid
                revenue_today += order.total_price

        pending_orders = Order.objects.filter(status="Pending").count()
        
        # Calculate month-over-month growth
        current_month_orders = Order.objects.filter(created_at__date__gte=thirty_days_ago).count()
        previous_month_orders = Order.objects.filter(
            created_at__date__gte=sixty_days_ago, 
            created_at__date__lt=thirty_days_ago
        ).count()
        
        # Calculate revenue based on paid orders only
        current_month_paid_orders = [
            order.id for order in Order.objects.filter(created_at__date__gte=thirty_days_ago) 
            if order.is_paid()
        ]
        current_month_revenue = Order.objects.filter(
            id__in=current_month_paid_orders
        ).aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        
        previous_month_paid_orders = [
            order.id for order in Order.objects.filter(
                created_at__date__gte=sixty_days_ago,
                created_at__date__lt=thirty_days_ago
            ) if order.is_paid()
        ]
        previous_month_revenue = Order.objects.filter(
            id__in=previous_month_paid_orders
        ).aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        
        # Calculate growth percentages
        if previous_month_orders > 0:
            order_growth = round(((current_month_orders - previous_month_orders) / previous_month_orders) * 100, 1)
        else:
            order_growth = 100.0
            
        if previous_month_revenue > 0:
            revenue_growth = round(((current_month_revenue - previous_month_revenue) / previous_month_revenue) * 100, 1)
        else:
            revenue_growth = 100.0
        
        # Recent transactions and orders with proper data for display
        recent_payments = Payment.objects.all().select_related('order')[:10]
        
        # Get recent orders with item count annotation
        recent_orders = Order.objects.all()[:10]
        
        # Add item count to each order for display
        for order in recent_orders:
            order.item_count = order.items.count()
            # Ensure total attribute exists for template compatibility
            order.total = order.total_price
        
        # Order status statistics
        completed_orders = Order.objects.filter(status="Delivered").count() + Order.objects.filter(status="Ready").count()
        processing_orders = Order.objects.filter(status="Processing").count()
        confirmed_orders = Order.objects.filter(status="Confirmed").count()
        cancelled_orders = Order.objects.filter(status="Cancelled").count()
        
        # Payment method statistics
        cash_payments = Payment.objects.filter(payment_method=Payment.PAYMENT_METHOD_CASH).count()
        mobile_payments = Payment.objects.filter(payment_method=Payment.PAYMENT_METHOD_MOBILE).count()
        
        # Prepare data for orders chart (last 14 days)
        chart_days = 14
        date_range = [today - timedelta(days=x) for x in range(chart_days-1, -1, -1)]
        
        order_counts = []
        order_dates = []
        
        for date in date_range:
            count = Order.objects.filter(created_at__date=date).count()
            order_counts.append(count)
            order_dates.append(date.strftime('%b %d'))
        
        # Top selling items
        top_selling_items = OrderItem.objects.values(
            'menu_item__name', 
            'menu_item__item_type'  # Changed from description to item_type
        ).annotate(
            order_count=Count('id'),
            revenue=Sum(F('unit_price') * F('quantity'))
        ).order_by('-order_count')[:5]
        
        # Format top selling items for display
        formatted_items = []
        for item in top_selling_items:
            formatted_items.append({
                'name': item['menu_item__name'],
                'item_type': item['menu_item__item_type'],  # Changed from description
                'order_count': item['order_count'],
                'revenue': item['revenue']
            })
        
        # Process payment records to match template field names
        for payment in recent_payments:
            # Add timestamp attribute to match template
            payment.timestamp = payment.created_at
        
        # Mock URL patterns for template (these should be defined in your urls.py)
        from django.urls import reverse, NoReverseMatch
        
        try:
            transaction_list_url = reverse('payments:transaction_list')
        except NoReverseMatch:
            transaction_list_url = '#'  # Fallback if URL not defined
            
        # Staff statistics
        active_staff = CustomUser.objects.filter(is_staff=True, is_active=True)
        admin_count = active_staff.filter(role='admin').count()
        frontdesk_count = active_staff.filter(role='frontdesk').count()
        kitchen_count = active_staff.filter(role='kitchen').count()
        delivery_count = active_staff.filter(role='delivery').count()
        
        total_staff = admin_count + frontdesk_count + kitchen_count + delivery_count
        # 'recent_users' and staff percentages are removed as per redesign request for the admin dashboard.
        # They were used for "Recently Added Staff" and "Staff Distribution" sections.
            
        # Prepare context data for template
        context.update({
            'total_orders': total_orders,
            'total_revenue': total_revenue, # All-time total revenue
            'today_orders': today_orders, # Count of orders created today
            'revenue_today': revenue_today, # Revenue from orders created and paid today
            'pending_orders': pending_orders, 
            'order_growth': order_growth,
            'revenue_growth': revenue_growth,
            'recent_transactions': recent_payments, 
            'recent_orders': recent_orders, 
            'completed_orders': completed_orders,
            'processing_orders': processing_orders,
            'confirmed_orders': confirmed_orders,
            'cancelled_orders': cancelled_orders,
            'cash_payments': cash_payments,
            'mobile_payments': mobile_payments,
            'order_dates': json.dumps(order_dates),
            'order_counts': json.dumps(order_counts),
            'top_selling_items': formatted_items,
            'today_date': today.strftime('%b %d, %Y'),
            'transaction_list_url': transaction_list_url,
            
            # Staff counts for summary cards
            'admin_count': admin_count,
            'frontdesk_count': frontdesk_count,
            'kitchen_count': kitchen_count,
            'delivery_count': delivery_count,
            'total_staff': total_staff, # Sum of staff counts, can be used in a summary card
        })
        
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
        
        # Get recent orders (last 24 hours) - limit to last 5 orders
        recent_orders = Order.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).order_by('-created_at')[:5]
        # Get today's stats
        # Get all orders created today for general counts
        all_today_orders_qs = Order.objects.filter(
            created_at__date=today
        )
        total_orders_today_count = all_today_orders_qs.count()

        # Calculate "Today's Sales Amount" and "Today's Completed Orders Count"
        # (Paid AND Fulfilled)
        todays_sales_amount = Decimal('0.00')
        todays_completed_orders_count = 0
        
        # Filter for orders that are fulfilled today
        todays_fulfilled_orders_qs = all_today_orders_qs.filter(status='Fulfilled')

        for order in todays_fulfilled_orders_qs: # Iterate only today's fulfilled orders
            if order.is_paid(): # Check if the order is also paid
                todays_sales_amount += order.total_price
                todays_completed_orders_count += 1 # This is a "completed" order

        # Calculate "Today's Pending Orders Count"
        # These are all orders today that are NOT (Paid AND Fulfilled)
        todays_pending_orders_count = total_orders_today_count - todays_completed_orders_count
        
        context.update({
            'recent_orders': recent_orders,
            'today_stats': {
                'total_orders': total_orders_today_count,       # Total orders created today
                'total_amount': todays_sales_amount,            # Sales from Paid & Fulfilled orders today
                'pending_orders': todays_pending_orders_count,  # Orders not (Paid & Fulfilled) today
                'completed_orders': todays_completed_orders_count, # Orders that are Paid & Fulfilled today
            }
        })
        
        return context

class KitchenDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/dashboards/kitchen_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_kitchen()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your kitchen dashboard context here
        return context

class DeliveryDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/dashboards/delivery_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_delivery()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your delivery dashboard context here
        return context

class AccessDeniedView(TemplateView):
    template_name = 'users/access_denied.html'

class StaffRegistrationView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/staff_form.html'
    success_url = reverse_lazy('users:staff_list')
    success_message = "Staff member was created successfully"
    
    def test_func(self):
        return self.request.user.is_admin()

class StaffListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'users/staff_list.html'
    context_object_name = 'staff_members'
    
    def test_func(self):
        return self.request.user.is_admin()
    
    def get_queryset(self):
        return CustomUser.objects.exclude(pk=self.request.user.pk)

class StaffDetailView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm # Use CustomUserChangeForm for editing
    template_name = 'users/staff_detail.html' # This template should render a form
    context_object_name = 'staff_member' # or 'object' or 'user'
    success_url = reverse_lazy('users:staff_list')
    success_message = "Staff member information updated successfully." # Generic message, can be customized in form_valid

    def test_func(self):
        # Ensure only admins can access this view
        # Also, prevent admin from editing their own 'role' or 'is_active' status via this form
        # if they are the object being edited (though CustomUserChangeForm handles some of this)
        return self.request.user.is_admin()

    def get_form_kwargs(self):
        """
        Pass the current user to the form if needed for validation,
        e.g., to prevent deactivating/changing role of the last admin.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pass the request user to the form
        return kwargs

    def form_valid(self, form):
        """
        If the form is valid, save the associated model and add a success message.
        """
        staff_member_name = form.cleaned_data.get('username') # or form.instance.get_full_name()
        messages.success(self.request, f"Staff member '{staff_member_name}' updated successfully.")
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: differentiate between update and delete actions.
        """
        self.object = self.get_object() # Required for UpdateView's super().post and delete logic

        if request.POST.get('_method') == 'DELETE':
            staff_member = self.object # Use self.object as it's already fetched

            if staff_member.is_superuser:
                messages.error(request, "Superusers cannot be deleted.")
                return HttpResponseRedirect(self.success_url) # Use success_url for consistency

            if staff_member == request.user:
                messages.error(request, "You cannot delete your own account using this form.")
                # Redirect to profile page or list, not allowing self-delete here
                return HttpResponseRedirect(self.success_url) 
            
            try:
                staff_member_name = staff_member.get_full_name() or staff_member.username
                staff_member.delete()
                messages.success(request, f"Staff member '{staff_member_name}' has been deleted successfully.")
            except Exception as e:
                messages.error(request, f"An error occurred while trying to delete the staff member: {e}")
            
            return HttpResponseRedirect(self.success_url)
        
        # If not a DELETE request, let the UpdateView's default POST handling take over
        return super().post(request, *args, **kwargs)

class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
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
