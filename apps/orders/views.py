from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Sum
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.contrib import messages

from .models import Order, OrderItem, OrderItemExtra
from .forms import OrderForm, OrderItemForm, OrderItemExtraForm, OrderWithItemsForm
from apps.menu.models import MenuItem, Extra


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access"""
    def test_func(self):
        return self.request.user.is_staff


# Order Views
class OrderListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """View to list all orders"""
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by delivery type if provided
        delivery_type = self.request.GET.get('delivery_type')
        if delivery_type:
            queryset = queryset.filter(delivery_type=delivery_type)
        
        # Search by customer name, phone, or location
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(customer_name__icontains=search_query) |
                Q(customer_phone__icontains=search_query) |
                Q(delivery_location__icontains=search_query)
            )
        
        # Sorting options
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by == 'total_price':
            queryset = queryset.order_by('-total_price')
        elif sort_by == 'customer':
            queryset = queryset.order_by('customer_name')
        else:  # Default to sort by creation date
            queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['delivery_choices'] = Order.DELIVERY_CHOICES
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_delivery'] = self.request.GET.get('delivery_type', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['sort_by'] = self.request.GET.get('sort', '-created_at')
        return context


class OrderDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View to display order details"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get order items with their extras
        context['items'] = self.object.items.prefetch_related('extras').all()
        return context


class OrderCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    View for creating a new order with customer information and items in one step
    """
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_create.html'
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create empty formset for order items
        OrderItemFormset = inlineformset_factory(
            Order, OrderItem, form=OrderItemForm, 
            extra=1, can_delete=True
        )
        
        if self.request.method == 'POST':
            context['formset'] = OrderItemFormset(self.request.POST, prefix='items')
        else:
            context['formset'] = OrderItemFormset(prefix='items')
        
        context['title'] = 'Create New Order'
        context['button_text'] = 'Create Order'
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            # Save the order first without committing to get an ID
            self.object = form.save()
            
            # Now save the formset with the order instance
            formset.instance = self.object
            formset.save()
            
            # Process extras for each order item
            for item_form in formset.forms:
                if not item_form.cleaned_data.get('DELETE', False) and item_form.instance.pk:
                    order_item = item_form.instance
                    extras_data = self.request.POST.getlist(f'item_{order_item.id}_extras')
                    quantities = self.request.POST.getlist(f'item_{order_item.id}_quantities')
                    
                    # Create extras for this order item
                    for i, extra_id in enumerate(extras_data):
                        if extra_id:
                            extra = Extra.objects.get(pk=extra_id)
                            quantity = int(quantities[i]) if i < len(quantities) else 1
                            
                            OrderItemExtra.objects.create(
                                order_item=order_item,
                                extra=extra,
                                quantity=quantity,
                                unit_price=extra.price
                            )
            
            # Recalculate the order's total price
            self.object.save()  # This will trigger the calculate_total method
            
            messages.success(self.request, f'Order #{self.object.id} created successfully!')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class OrderUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """View to update an existing order"""
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_update.html'
    context_object_name = 'order'
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create formset for order items
        OrderItemFormset = inlineformset_factory(
            Order, OrderItem, form=OrderItemForm, 
            extra=1, can_delete=True
        )
        
        if self.request.method == 'POST':
            context['formset'] = OrderItemFormset(
                self.request.POST, prefix='items', instance=self.object
            )
        else:
            context['formset'] = OrderItemFormset(
                prefix='items', instance=self.object
            )
            
        # Get existing items with their extras for the template
        context['items_with_extras'] = []
        for item in self.object.items.all():
            extras = item.extras.all()
            context['items_with_extras'].append({
                'item': item,
                'extras': extras
            })
            
        context['title'] = f'Update Order #{self.object.id}'
        context['button_text'] = 'Save Changes'
        return context
    
    def form_valid(self, form):
        # Process the main form
        self.object = form.save()
        
        # Process the formset for order items
        OrderItemFormset = inlineformset_factory(
            Order, OrderItem, form=OrderItemForm, 
            extra=1, can_delete=True
        )
        formset = OrderItemFormset(self.request.POST, prefix='items', instance=self.object)
        
        if formset.is_valid():
            formset.save()
            
            # Process extras for each order item
            for item_form in formset.forms:
                if not item_form.cleaned_data.get('DELETE', False) and item_form.instance.pk:
                    order_item = item_form.instance
                    
                    # Handle extras for this order item
                    # First, get extras data from POST
                    extras_data = self.request.POST.getlist(f'item_{order_item.id}_extras')
                    quantities = self.request.POST.getlist(f'item_{order_item.id}_quantities')
                    
                    # Delete all existing extras that are not in the new data
                    existing_extras = set(str(e.extra.id) for e in order_item.extras.all())
                    new_extras = set(extra_id for extra_id in extras_data if extra_id)
                    
                    # Delete extras that were removed
                    extras_to_delete = existing_extras - new_extras
                    if extras_to_delete:
                        order_item.extras.filter(extra__id__in=extras_to_delete).delete()
                    
                    # Update or create extras
                    for i, extra_id in enumerate(extras_data):
                        if extra_id:
                            quantity = int(quantities[i]) if i < len(quantities) else 1
                            extra = Extra.objects.get(pk=extra_id)
                            
                            # Try to get existing extra or create new one
                            try:
                                item_extra = order_item.extras.get(extra=extra)
                                # Update quantity if changed
                                if item_extra.quantity != quantity:
                                    item_extra.quantity = quantity
                                    item_extra.save()
                            except OrderItemExtra.DoesNotExist:
                                # Create new extra
                                OrderItemExtra.objects.create(
                                    order_item=order_item,
                                    extra=extra,
                                    quantity=quantity,
                                    unit_price=extra.price
                                )
            
            # Recalculate the order's total price
            self.object.save()  # This will trigger the calculate_total method
            
            messages.success(self.request, f'Order #{self.object.id} updated successfully!')
            return redirect(self.get_success_url())
        else:
            # If formset is invalid, re-render with errors
            return self.form_invalid(form)


class OrderStatusUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """View to quickly update order status"""
    model = Order
    fields = ['status']
    template_name = 'orders/order_status_update.html'
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        previous_status = Order.objects.get(pk=self.object.pk).status
        response = super().form_valid(form)
        new_status = self.object.status
        
        # Add success message with status change details
        messages.success(
            self.request, 
            f'Order #{self.object.id} status changed from {previous_status} to {new_status}.'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Update Status for Order #{self.object.id}'
        context['button_text'] = 'Update Status'
        context['order'] = self.object
        return context
