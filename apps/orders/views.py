from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Sum
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views.decorators.http import require_POST
from django.db import transaction
import traceback
import datetime # Added import
from django.utils import timezone # Ensure timezone is imported
from decimal import Decimal

from .models import Order, OrderItem, DELIVERY_FEES # Add DELIVERY_FEES here
from .forms import OrderForm, OrderItemForm, OrderWithItemsForm
from apps.menu.models import MenuItem
from apps.payments.models import Payment


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
        
        # Search by customer name, phone, location, or order number
        search_query = self.request.GET.get('search')
        if search_query:
            q_objects = Q(customer_name__icontains=search_query) | \
                        Q(customer_phone__icontains=search_query) | \
                        Q(delivery_location__icontains=search_query) | \
                        Q(order_number__icontains=search_query) # General search for order number

            # If the search query is exactly 3 digits, also try matching the end of the order number
            if search_query.isdigit() and len(search_query) == 3:
                q_objects |= Q(order_number__endswith=f"-{search_query}")
            
            queryset = queryset.filter(q_objects)

        # Date filtering
        date_filter_str = self.request.GET.get('date')
        self.target_date = timezone.localdate() # Default to today
        if date_filter_str:
            try:
                self.target_date = datetime.datetime.strptime(date_filter_str, '%Y-%m-%d').date()
            except ValueError:
                # Invalid date string, target_date remains today.
                # Optionally, add a message to the user:
                # messages.warning(self.request, "Invalid date format. Showing orders for today.")
                pass 
        
        queryset = queryset.filter(created_at__date=self.target_date)
        
        # Default sort order
        queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        
        # Prepare STATUS_CHOICES for JavaScript
        status_choices_for_js = [{'value': choice[0], 'display': choice[1]} for choice in Order.STATUS_CHOICES]
        context['status_choices_json'] = json.dumps(status_choices_for_js)

        # Date for picker and display
        # self.target_date should be set by get_queryset
        target_date_obj = getattr(self, 'target_date', timezone.localdate()) # Fallback if get_queryset didn't set it
        context['selected_date_for_picker'] = target_date_obj.strftime('%Y-%m-%d')
        context['display_date_header'] = target_date_obj.strftime('%B %d, %Y')
        
        return context


class OrderDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View to display order details"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        all_items_qs = self.object.items.select_related('menu_item').order_by('created_at')
        all_items_list = list(all_items_qs)

        structured_items = []
        extras_map = {}  # To hold extras, keyed by their parent_item_id

        # First pass: Separate main items and map extras
        for item in all_items_list: # Iterate over the list
            if item.parent_item_id is None:
                # This is a main item
                structured_items.append({
                    'item_instance': item,
                    'menu_item_name': item.menu_item.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'subtotal': item.subtotal,
                    'notes': item.notes,
                    'is_extra': False,
                    'extras': []  # Placeholder for its extras
                })
            else:
                # This is an extra item
                if item.parent_item_id not in extras_map:
                    extras_map[item.parent_item_id] = []
                extras_map[item.parent_item_id].append({
                    'item_instance': item, # Good to have the instance if needed
                    'menu_item_name': item.menu_item.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'subtotal': item.subtotal,
                    'notes': item.notes,
                    'is_extra': True
                })
        
        # Second pass: Attach extras to their main items in structured_items
        for main_item_dict in structured_items:
            parent_instance_id = main_item_dict['item_instance'].id
            if parent_instance_id in extras_map:
                main_item_dict['extras'] = extras_map[parent_instance_id]
                
        context['structured_order_items'] = structured_items
        
        status_choices_for_js = [{'value': choice[0], 'display': choice[1]} for choice in Order.STATUS_CHOICES]
        context['status_choices_json'] = json.dumps(status_choices_for_js)

        # Calculate total payments and refunds
        order = self.object
        total_payments_received = order.payments.filter(
            status=Payment.STATUS_COMPLETED,
            payment_type=Payment.PAYMENT_TYPE_PAYMENT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_refunds_issued = order.payments.filter(
            status=Payment.STATUS_COMPLETED,
            payment_type=Payment.PAYMENT_TYPE_REFUND
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        context['total_payments_received'] = total_payments_received
        context['total_refunds_issued'] = total_refunds_issued
        context['has_completed_refunds'] = order.payments.filter(
            status=Payment.STATUS_COMPLETED,
            payment_type=Payment.PAYMENT_TYPE_REFUND
        ).exists()

        # Determine if the refund button should be shown
        is_overpaid = order.amount_overpaid() > Decimal('0.00')
        # is_partially_paid = order.amount_paid() > Decimal('0.00') and order.balance_due() > Decimal('0.00') # No longer used directly for can_process_refund
        
        # Refund button should appear only if the order is OVERPAID
        # and no refunds have been completed yet.
        context['can_process_refund'] = is_overpaid and not context['has_completed_refunds']
        context['show_overpaid_amount'] = is_overpaid # This variable is used to display the "Amount Overpaid" section
        
        return context


def get_order_items_json(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    all_items_qs = order.items.select_related('menu_item').order_by('created_at')
    
    structured_items_for_json = []
    extras_map_for_json = {} # Keyed by parent_item_id

    for item in all_items_qs:
        item_data = {
            'menu_item_name': item.menu_item.name,
            'quantity': item.quantity,
            'unit_price': f"{item.unit_price:.2f}" if item.unit_price is not None else "0.00",
            'subtotal': f"{item.subtotal:.2f}" if item.subtotal is not None else "0.00",
            'notes': item.notes or "",
            'is_extra': item.parent_item_id is not None,
            'extras': [] 
        }
        if item.parent_item_id is None: # Main item
            # Store the original item pk to link extras later if needed, though not strictly necessary for json if flat
            item_data['db_item_pk'] = item.pk 
            structured_items_for_json.append(item_data)
        else: # Extra item
            if item.parent_item_id not in extras_map_for_json:
                extras_map_for_json[item.parent_item_id] = []
            # For extras, we don't add 'db_item_pk' or 'extras' list to item_data itself here
            # as they are simpler structures.
            extra_item_data_simplified = {
                'menu_item_name': item.menu_item.name,
                'quantity': item.quantity,
                'unit_price': f"{item.unit_price:.2f}" if item.unit_price is not None else "0.00",
                'subtotal': f"{item.subtotal:.2f}" if item.subtotal is not None else "0.00",
                'notes': item.notes or "",
                'is_extra': True
            }
            extras_map_for_json[item.parent_item_id].append(extra_item_data_simplified)

    # Attach extras to their main items
    for main_item_dict in structured_items_for_json:
        parent_db_item_pk = main_item_dict.pop('db_item_pk') # Remove the temporary key
        if parent_db_item_pk in extras_map_for_json:
            main_item_dict['extras'] = extras_map_for_json[parent_db_item_pk]
            
    return JsonResponse({'items': structured_items_for_json})

class OrderCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    View for creating a new order with customer information and items in one step
    """
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_create.html'
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'order_number': self.object.order_number})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create empty formset for order items
        OrderItemFormset = inlineformset_factory(
            Order, OrderItem, form=OrderItemForm, 
            extra=1, can_delete=True
        )
        
        form_init_kwargs = {'item_type_filter': 'regular'}
        if self.request.method == 'POST':
            context['formset'] = OrderItemFormset(self.request.POST, prefix='items', form_kwargs=form_init_kwargs)
            context['formset_is_bound'] = True 
        else:
            context['formset'] = OrderItemFormset(prefix='items', form_kwargs=form_init_kwargs)
            context['formset_is_bound'] = False
        
        context['title'] = 'Create New Order'
        context['button_text'] = 'Create Order'

        # Add available extras to the context for JavaScript
        available_extras_data = list(MenuItem.objects.filter(item_type='extra', is_available=True).values('id', 'name', 'price'))
        context['available_extras_data'] = available_extras_data
        context['DELIVERY_FEES'] = DELIVERY_FEES
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context.get('formset') 

        if item_formset is None:
            messages.error(self.request, "Error: Item formset not found.")
            return self.render_to_response(self.get_context_data(form=form))

        if form.is_valid() and item_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.save()

            saved_main_items = {}

            # First Pass: Saving Main Items
            for i, item_form in enumerate(item_formset.forms):
                if item_form.is_valid() and item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                    # MODIFICATION HERE: Read the field JS is sending ('parent_item_ref')
                    parent_ref_field_name = f'{item_form.prefix}-parent_item_ref' 
                    parent_item_ref_value = self.request.POST.get(parent_ref_field_name, None)
                    
                    # Determine if this item IS an extra based on the presence of parent_item_ref_value
                    is_extra_submission = bool(parent_item_ref_value)

                    if not is_extra_submission: # This is a main item
                        order_item = item_form.save(commit=False)
                        order_item.order = self.object
                        order_item.parent_item = None
                        if not order_item.unit_price and order_item.menu_item:
                             order_item.unit_price = order_item.menu_item.price
                        order_item.save()
                        saved_main_items[str(i)] = order_item # Store by its own form index
                    # else:
                        # This item has a parent_item_ref, so it's an extra and will be processed in the next loop.
                        # print(f"    Skipped as MAIN (has parent_item_ref_value), will process as EXTRA: Form {i}, Name='{item_form.cleaned_data.get('menu_item')}'")
            
            # Second Pass: Saving Extra Items
            for i, item_form in enumerate(item_formset.forms):
                if item_form.is_valid() and item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                    # MODIFICATION HERE: Read 'parent_item_ref' and parse it
                    parent_ref_field_name = f'{item_form.prefix}-parent_item_ref'
                    parent_item_ref_value = self.request.POST.get(parent_ref_field_name, None)
                    
                    parent_form_index_str = None # This will be the actual index string (e.g., "0")
                    if parent_item_ref_value:
                        # Expected format "items-0", "items-1", etc.
                        parts = parent_item_ref_value.split('-')
                        if len(parts) > 1: # Ensure there's at least a prefix and an index
                            parent_form_index_str = parts[-1] # Get the last part, which should be the index

                    if parent_form_index_str is not None: # This is an extra AND we got an index
                        order_item = item_form.save(commit=False)
                        order_item.order = self.object
                        
                        parent_instance = saved_main_items.get(parent_form_index_str) # Use the parsed index
                        if parent_instance:
                            order_item.parent_item = parent_instance
                        else:
                            messages.error(self.request, f"Error: Could not find parent item for an extra (parsed parent index: {parent_form_index_str}). Extra '{order_item.menu_item.name if order_item.menu_item else 'Unknown Item'}' saved without parent link.")
                            order_item.parent_item = None
                        
                        if not order_item.unit_price and order_item.menu_item:
                             order_item.unit_price = order_item.menu_item.price
                        order_item.save()
                    elif parent_item_ref_value and parent_form_index_str is None:
                        # parent_item_ref_value was present but couldn't be parsed to an index.
                        # Decide if you want to save it as a main item or log error and skip
                        if str(i) not in saved_main_items: # If it wasn't already saved as a main item
                            order_item = item_form.save(commit=False)
                            order_item.order = self.object
                            order_item.parent_item = None
                            if not order_item.unit_price and order_item.menu_item:
                                order_item.unit_price = order_item.menu_item.price
                            order_item.save()


            self.object.calculate_total() 
            self.object.save(update_fields=['total_price']) 

            messages.success(self.request, f'Order #{self.object.order_number} created successfully.') # Simplified message
            return HttpResponseRedirect(self.get_success_url())
        else:
            # ... (error handling remains the same) ...
            error_messages_list = []
            if form.errors:
                for field, errors in form.errors.items():
                    error_messages_list.append(f"Order Details - {form.fields[field].label if field != '__all__' else 'General'}: {'; '.join(errors)}")
            if item_formset.non_form_errors():
                 for error in item_formset.non_form_errors():
                    error_messages_list.append(f"Order Items (General): {error}")
            for i, item_f_errors in enumerate(item_formset.errors):
                if item_f_errors:
                    form_prefix_for_error_item = item_formset.forms[i].prefix
                    item_label = f"Item #{i+1}" 
                    try:
                        menu_item_pk = self.request.POST.get(f"{form_prefix_for_error_item}-menu_item")
                        if menu_item_pk:
                            menu_item_obj = MenuItem.objects.get(pk=menu_item_pk)
                            item_label = f"Item '{menu_item_obj.name}'"
                    except Exception:
                        pass 
                    for field, errors in item_f_errors.items():
                         field_label = item_formset.forms[i].fields[field].label if field in item_formset.forms[i].fields else field
                         error_messages_list.append(f"{item_label} - {field_label}: {'; '.join(errors)}")
            
            messages.error(self.request, "Please correct the errors: " + " | ".join(error_messages_list))
            return self.render_to_response(self.get_context_data(form=form, formset=item_formset))

    def form_invalid(self, form):
        messages.error(self.request, "There were errors in the main order details. Please check the fields below.")
        return self.render_to_response(self.get_context_data(form=form))

class OrderUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """View to update an existing order"""
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_update.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'order_number': self.object.order_number})
    
    def get_formset_class(self):
        """Get the formset class with consistent configuration"""
        return inlineformset_factory(
            Order, OrderItem, 
            form=OrderItemForm,  # Use our custom form that already handles price_display
            extra=0,  # Changed to 0 to prevent automatic extra form
            can_delete=True, 
            min_num=1, 
            validate_min=True,
            fields=['menu_item', 'quantity', 'unit_price', 'parent_item'],
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the formset
        OrderItemFormset = self.get_formset_class()
        
        if 'formset' not in kwargs:
            # Get existing order items with their original prices
            existing_items = OrderItem.objects.filter(
                order=self.object
            ).select_related('menu_item')

            if self.request.POST:
                # For POST requests, initialize with submitted data
                context['formset'] = OrderItemFormset(
                    self.request.POST,
                    prefix='items',
                    instance=self.object,
                    queryset=existing_items
                )
            else:
                # For GET requests, initialize with existing data
                context['formset'] = OrderItemFormset(
                    prefix='items',
                    instance=self.object,
                    queryset=existing_items,
                    initial=[{
                        'menu_item': item.menu_item,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'price_display': item.unit_price  # This will show in the display field
                    } for item in existing_items]
                )
        
        # Add available extras to the context for JavaScript
        available_extras_data = list(MenuItem.objects.filter(item_type='extra', is_available=True).values('id', 'name', 'price'))
        context['available_extras_data'] = available_extras_data
        context['DELIVERY_FEES'] = DELIVERY_FEES

        context['title'] = f'Update Order #{self.object.order_number}'
        context['button_text'] = 'Save Changes'
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        try:
            self.object = form.save() 
            
            deleted_items_info = []
            new_items_info = []
            updated_items_info = []
            
            if not formset.is_valid():
                messages.error(self.request, "Please correct the errors in the order items (formset invalid).")
                return self.form_invalid(form)

            # Store saved main items by their form prefix to link extras later
            # A main item is one that is not an extra itself (has no parent_item_ref)
            saved_main_items_by_prefix = {}

            # Stage 1: Handle deletions (remains mostly the same)
            for item_form_idx, item_form in enumerate(formset.forms):
                if formset.can_delete and item_form.cleaned_data.get('DELETE', False):
                    if item_form.instance.pk: 
                        item_to_delete = item_form.instance
                        # If it's a parent item, its children (extras) will be deleted by CASCADE if parent_item FK is set up.
                        deleted_items_info.append(str(item_to_delete.menu_item.name if item_to_delete.menu_item else f"Item ID {item_to_delete.pk}"))
                        item_to_delete.delete()
            
            # Stage 2: Process and Save MAIN items first (items that are NOT extras)
            for item_form_idx, item_form in enumerate(formset.forms):
                if not (formset.can_delete and item_form.cleaned_data.get('DELETE', False)): # If not marked for deletion
                    # Check if this form is for an extra by looking for parent_item_ref in POST data
                    # An item is a MAIN item if it does NOT have a parent_item_ref
                    parent_ref_key = f"{item_form.prefix}-parent_item_ref"
                    parent_item_form_prefix_ref = self.request.POST.get(parent_ref_key)
                    
                    is_extra_item_submission = bool(parent_item_form_prefix_ref)
                    # Also consider if the menu_item itself is of type 'extra', for existing items being re-saved
                    menu_item_is_extra_type = item_form.cleaned_data.get('menu_item') and item_form.cleaned_data['menu_item'].item_type == 'extra'

                    # A main item is one that is not submitted as an extra (no parent_item_ref) 
                    # AND whose menu_item is not of type 'extra' (unless it's an existing item that was an extra but parent_ref was lost).
                    # For simplicity now: if it has parent_item_ref, it's an extra. Otherwise, it's a main item.
                    # We will refine the definition of an "extra" when we process extras.

                    if not is_extra_item_submission: # This is a MAIN item
                        if item_form.has_changed() or not item_form.instance.pk:
                            instance = item_form.save(commit=False)
                            instance.order = self.object 
                            instance.parent_item = None # Explicitly ensure main items have no parent
                            
                            instance.save() 
                            saved_main_items_by_prefix[item_form.prefix] = instance # Store by form prefix

                            if not item_form.instance.pk or item_form.instance.pk != instance.pk : # if it was a new item (no initial pk)
                                new_items_info.append(instance.menu_item.name if instance.menu_item else "Unknown Main Item")
                            else: # it was an existing item that changed
                                updated_items_info.append(instance.menu_item.name if instance.menu_item else "Unknown Main Item")
                        elif item_form.instance.pk: # Existing main item, unchanged but still need to track it for potential extras
                             saved_main_items_by_prefix[item_form.prefix] = item_form.instance

            # Stage 3: Process and Save EXTRA items, linking them to their parents
            for item_form_idx, item_form in enumerate(formset.forms):
                if not (formset.can_delete and item_form.cleaned_data.get('DELETE', False)): # If not marked for deletion
                    parent_ref_key = f"{item_form.prefix}-parent_item_ref"
                    parent_item_form_prefix_ref = self.request.POST.get(parent_ref_key)

                    if parent_item_form_prefix_ref: # This form is for an EXTRA item
                        if item_form.has_changed() or not item_form.instance.pk:
                            extra_instance = item_form.save(commit=False)
                            extra_instance.order = self.object

                            parent_main_item_instance = saved_main_items_by_prefix.get(parent_item_form_prefix_ref)
                            if parent_main_item_instance:
                                extra_instance.parent_item = parent_main_item_instance
                            else:
                                # Log or handle error: Parent item not found
                                extra_instance.parent_item = None # Or handle error

                            extra_instance.save()
                            
                            # Decide if it's new or updated based on its own PK status
                            if not item_form.instance.pk or item_form.instance.pk != extra_instance.pk: # if it was a new extra item
                                new_items_info.append(f"{extra_instance.menu_item.name} (Extra)" if extra_instance.menu_item else "Unknown Extra")
                            else: # it was an existing extra item that changed
                                updated_items_info.append(f"{extra_instance.menu_item.name} (Extra)" if extra_instance.menu_item else "Unknown Extra")
                        # If an existing extra item is unchanged, it's already linked (or should be), so no specific action here.
                        # The formset handles existing instances correctly if they don't change.
            
            self.object.save() 
            
            message_parts = [f'Order #{self.object.order_number or self.object.id} updated successfully!']
            if deleted_items_info:
                message_parts.append(f"Removed: {', '.join(deleted_items_info)}")
            if new_items_info:
                message_parts.append(f"Added: {', '.join(new_items_info)}")
            if updated_items_info:
                message_parts.append(f"Updated: {', '.join(updated_items_info)}")
            
            success_msg = " | ".join(message_parts)
            messages.success(self.request, success_msg)
            return redirect(self.get_success_url())
            
        except Exception as e:
            # import traceback # Keep for debugging if needed
            # traceback.print_exc() 
            messages.error(self.request, f"CRITICAL Error updating order: {str(e)}. Please check logs.")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There were errors in your form. Please check and try again.")
        return self.render_to_response(self.get_context_data(form=form))


class OrderStatusUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """View to quickly update order status"""
    model = Order
    form_class = OrderForm # Use OrderForm to include conditional status logic
    template_name = 'orders/order_status_update.html'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def get_form_kwargs(self):
        """Pass the instance to the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.object})
        return kwargs

    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'order_number': self.object.order_number})
    
    def form_valid(self, form):
        # self.object is already loaded by order_number due to slug_field/slug_url_kwarg
        # To get the status *before* super().form_valid() potentially changes it,
        # we fetch a fresh instance or rely on the currently loaded self.object's status if it hasn't been altered by the form yet.
        # For safety, fetching a fresh instance ensures we get the DB state.
        previous_status = Order.objects.get(order_number=self.object.order_number).status
        response = super().form_valid(form)
        new_status = self.object.status
        
        messages.success(
            self.request, 
            f'Order #{self.object.order_number} status changed from {previous_status} to {new_status}.'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Update Status for Order #{self.object.order_number}'
        context['button_text'] = 'Update Status'
        context['order'] = self.object
        return context


# Helper function for AJAX status update badge class
def get_status_badge_class(status_value):
    mapping = {
        "Pending": "status-pending",
        "Accepted": "status-confirmed",
        "Ready": "status-ready",
        "Out for Delivery": "status-processing",
        "Fulfilled": "status-delivered",
        "Cancelled": "status-cancelled",
    }
    return mapping.get(status_value, "bg-secondary") # Default fallback


@require_POST # Ensures this view only accepts POST requests
def ajax_update_order_status(request, order_number):
    try:
        order = get_object_or_404(Order, order_number=order_number)
        new_status = request.POST.get('status')

        # Validate the new_status
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'errors': 'Invalid status value provided.'}, status=400)

        # Additional validation: Prevent "Out for Delivery" if order is "Pickup"
        if order.delivery_type == "Pickup" and new_status == "Out for Delivery":
            return JsonResponse({
                'success': False, 
                'errors': f'Cannot set status to "Out for Delivery" for a Pickup order.'
            }, status=400)

        if order.status == new_status:
            return JsonResponse({
                'success': True,
                'message': 'Status is already the same.',
                'order_number': order.order_number,
                'new_status_value': order.status,
                'new_status_display': order.get_status_display(),
                'new_status_badge_class': get_status_badge_class(order.status)
            })

        with transaction.atomic():
            order.status = new_status
            order.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'new_status_value': order.status,
            'new_status_display': order.get_status_display(),
            'new_status_badge_class': get_status_badge_class(order.status)
        })

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'errors': 'Order not found.'}, status=404)
    except Exception as e:
        # Log the exception e for server-side review
        # import traceback
        # traceback.print_exc() # for detailed logging during dev
        return JsonResponse({'success': False, 'errors': str(e)}, status=500)
