from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order

def frontdesk_required(function):
    """Decorator for views that checks that the user is frontdesk staff."""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_frontdesk or u.is_admin),
        login_url='users:login'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

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
