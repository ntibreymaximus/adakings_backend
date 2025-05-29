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
from django.core.serializers.json import DjangoJSONEncoder
import json
import traceback

from .models import Order, OrderItem
from .forms import OrderForm, OrderItemForm, OrderWithItemsForm
from apps.menu.models import MenuItem


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
        
        print(f"[OrderDetailView DEBUG] Getting items for Order PK: {self.object.pk}") # Debug line
        all_items_qs = self.object.items.select_related('menu_item').order_by('created_at')
        all_items_list = list(all_items_qs) # Convert to list to print and iterate
        
        print(f"[OrderDetailView DEBUG] Found {len(all_items_list)} raw items for Order PK {self.object.pk}:") # Debug line
        for i, db_item in enumerate(all_items_list):
            print(f"  DEBUG Raw Item {i}: Name='{db_item.menu_item.name}', Item_PK={db_item.pk}, Parent_Item_PK={db_item.parent_item_id}") # Debug line

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
        
        print(f"[OrderDetailView DEBUG] Processed into {len(structured_items)} structured main items for Order PK {self.object.pk}.") # Debug line
        for i, si_dict in enumerate(structured_items):
            print(f"  DEBUG Structured Main Item {i}: Name='{si_dict['menu_item_name']}', Num_Extras={len(si_dict['extras'])}") # Debug line
            for j, extra_dict in enumerate(si_dict['extras']):
                 print(f"    DEBUG Extra {j} for Main Item {i}: Name='{extra_dict['menu_item_name']}'") # Debug line
        
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
        
        return context
    
    def form_valid(self, form):
        # ... (initial prints are fine) ...
        print(f"[OrderCreateView DEBUG FormValid] ****** form_valid ENTERED ****** Request method: {self.request.method}")

        context = self.get_context_data()
        item_formset = context.get('formset') 

        print(f"[OrderCreateView DEBUG FormValid] Context type: {type(context)}")
        print(f"[OrderCreateView DEBUG FormValid] Item_formset type: {type(item_formset)}")
        if item_formset is not None:
            print(f"[OrderCreateView DEBUG FormValid] Item_formset prefix: {item_formset.prefix}")
            print(f"[OrderCreateView DEBUG FormValid] Is item_formset bound? {item_formset.is_bound}")
        else:
            print(f"[OrderCreateView DEBUG FormValid] item_formset IS NONE from context.get('formset')!")
        
        if item_formset is None:
            messages.error(self.request, "Error: Item formset not found.")
            return self.render_to_response(self.get_context_data(form=form))

        print(f"[OrderCreateView DEBUG FormValid] --- BEGIN All Raw POST Data ---")
        for key, value in self.request.POST.items():
            print(f"  Raw POST['{key}'] = '{value}'")
        print(f"[OrderCreateView DEBUG FormValid] --- END All Raw POST Data ---")

        if form.is_valid() and item_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.save()

            saved_main_items = {}

            print("[OrderCreateView DEBUG FormValid] --- First Pass: Saving Main Items ---")
            for i, item_form in enumerate(item_formset.forms):
                if item_form.is_valid() and item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                    
                    # MODIFICATION HERE: Read the field JS is sending ('parent_item_ref')
                    parent_ref_field_name = f'{item_form.prefix}-parent_item_ref' 
                    parent_item_ref_value = self.request.POST.get(parent_ref_field_name, None)
                    
                    # Determine if this item IS an extra based on the presence of parent_item_ref_value
                    is_extra_submission = bool(parent_item_ref_value)

                    print(f"  [Main Pass] Form {i} ({item_form.prefix}): parent_item_ref_value from POST = '{parent_item_ref_value}', is_extra_submission = {is_extra_submission}")

                    if not is_extra_submission: # This is a main item
                        order_item = item_form.save(commit=False)
                        order_item.order = self.object
                        order_item.parent_item = None
                        if not order_item.unit_price and order_item.menu_item:
                             order_item.unit_price = order_item.menu_item.price
                        order_item.save()
                        saved_main_items[str(i)] = order_item # Store by its own form index
                        print(f"    Saved as MAIN item: PK={order_item.pk}, Name='{order_item.menu_item.name}', Mapped from form index {i}")
                    else:
                        print(f"    Skipped as MAIN (has parent_item_ref_value), will process as EXTRA: Form {i}, Name='{item_form.cleaned_data.get('menu_item')}'")
            
            print(f"[OrderCreateView DEBUG FormValid] --- Second Pass: Saving Extra Items --- Found {len(saved_main_items)} potential parents.")
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
                    
                    print(f"  [Extra Pass] Form {i} ({item_form.prefix}): parent_item_ref_value='{parent_item_ref_value}', parsed parent_form_index_str = '{parent_form_index_str}'")

                    if parent_form_index_str is not None: # This is an extra AND we got an index
                        order_item = item_form.save(commit=False)
                        order_item.order = self.object
                        
                        parent_instance = saved_main_items.get(parent_form_index_str) # Use the parsed index
                        if parent_instance:
                            order_item.parent_item = parent_instance
                            print(f"    Linking EXTRA item (from form {i}, Name='{order_item.menu_item.name}') to PARENT (form index {parent_form_index_str}, PK={parent_instance.pk}, Name='{parent_instance.menu_item.name}')")
                        else:
                            messages.error(self.request, f"Error: Could not find parent item for an extra (parsed parent index: {parent_form_index_str}). Extra '{order_item.menu_item.name if order_item.menu_item else 'Unknown Item'}' saved without parent link.")
                            order_item.parent_item = None
                            print(f"    ERROR: Parent instance NOT FOUND for parent_form_index_str='{parent_form_index_str}'. Extra (from form {i}, Name='{order_item.menu_item.name}') will be saved with Parent_Item_PK=None.")
                        
                        if not order_item.unit_price and order_item.menu_item:
                             order_item.unit_price = order_item.menu_item.price
                        order_item.save()
                        print(f"    Saved as EXTRA item: PK={order_item.pk}, Name='{order_item.menu_item.name}', Parent_PK={order_item.parent_item_id if order_item.parent_item else 'None'}")
                    elif parent_item_ref_value and parent_form_index_str is None:
                        # parent_item_ref_value was present but couldn't be parsed to an index.
                        print(f"    WARNING: Item from form {i} had parent_item_ref_value='{parent_item_ref_value}' but it could not be parsed into a parent index. Item will not be linked as extra.")
                        # Decide if you want to save it as a main item or log error and skip
                        if str(i) not in saved_main_items: # If it wasn't already saved as a main item
                            order_item = item_form.save(commit=False)
                            order_item.order = self.object
                            order_item.parent_item = None
                            if not order_item.unit_price and order_item.menu_item:
                                order_item.unit_price = order_item.menu_item.price
                            order_item.save()
                            print(f"    Saved as fallback MAIN item due to parsing error: PK={order_item.pk}, Name='{order_item.menu_item.name}'")


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
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.object.pk})
    
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

        context['title'] = f'Update Order #{self.object.order_number}'
        context['button_text'] = 'Save Changes'
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        try:
            print(f"[OrderUpdateView] Starting form_valid for order PK {self.object.pk if self.object and hasattr(self.object, 'pk') else 'NEW_OR_NO_PK_YET'}")
            
            self.object = form.save() 
            print(f"[OrderUpdateView] Main order form saved. Order PK: {self.object.pk}, Customer: {self.object.customer_name}")
            
            deleted_items_info = []
            new_items_info = []
            updated_items_info = []
            
            print(f"[OrderUpdateView] Is formset valid? {formset.is_valid()}")
            if not formset.is_valid():
                print(f"[OrderUpdateView] FORMSET ERRORS: {formset.errors}")
                print(f"[OrderUpdateView] NON-FORM ERRORS: {formset.non_form_errors()}")
                messages.error(self.request, "Please correct the errors in the order items (formset invalid).")
                return self.form_invalid(form)

            print(f"[OrderUpdateView] Processing formset. Number of forms in formset: {len(formset.forms)}")

            # Store saved main items by their form prefix to link extras later
            # A main item is one that is not an extra itself (has no parent_item_ref)
            saved_main_items_by_prefix = {}

            # Stage 1: Handle deletions (remains mostly the same)
            for item_form_idx, item_form in enumerate(formset.forms):
                print(f"[OrderUpdateView DELETION_STAGE] Processing item_form {item_form_idx}, prefix: {item_form.prefix}")
                if formset.can_delete and item_form.cleaned_data.get('DELETE', False):
                    if item_form.instance.pk: 
                        item_to_delete = item_form.instance
                        # If it's a parent item, its children (extras) will be deleted by CASCADE if parent_item FK is set up.
                        deleted_items_info.append(str(item_to_delete.menu_item.name if item_to_delete.menu_item else f"Item ID {item_to_delete.pk}"))
                        print(f"[OrderUpdateView DELETION_STAGE] Deleting OrderItem instance: {item_to_delete} (PK: {item_to_delete.pk})")
                        item_to_delete.delete()
                        print(f"[OrderUpdateView DELETION_STAGE] Deleted OrderItem PK: {item_to_delete.pk}")
                    else:
                        print(f"[OrderUpdateView DELETION_STAGE] Item_form {item_form.prefix} marked DELETE but not an existing instance.")
            
            # Stage 2: Process and Save MAIN items first (items that are NOT extras)
            print(f"[OrderUpdateView SAVE_MAIN_ITEMS_STAGE] Starting to process and save MAIN items.")
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
                            
                            print(f"[OrderUpdateView SAVE_MAIN_ITEMS_STAGE] About to save MAIN OrderItem instance (from form {item_form.prefix}): Menu: {instance.menu_item}, Qty: {instance.quantity}")
                            instance.save() 
                            print(f"[OrderUpdateView SAVE_MAIN_ITEMS_STAGE] Saved MAIN OrderItem instance. PK: {instance.pk}, Form Prefix: {item_form.prefix}")
                            saved_main_items_by_prefix[item_form.prefix] = instance # Store by form prefix

                            if not item_form.instance.pk or item_form.instance.pk != instance.pk : # if it was a new item (no initial pk)
                                new_items_info.append(instance.menu_item.name if instance.menu_item else "Unknown Main Item")
                            else: # it was an existing item that changed
                                updated_items_info.append(instance.menu_item.name if instance.menu_item else "Unknown Main Item")
                        elif item_form.instance.pk: # Existing main item, unchanged but still need to track it for potential extras
                             print(f"[OrderUpdateView SAVE_MAIN_ITEMS_STAGE] Existing MAIN item (form {item_form.prefix}, PK {item_form.instance.pk}) was unchanged but tracked.")
                             saved_main_items_by_prefix[item_form.prefix] = item_form.instance
                    else:
                        print(f"[OrderUpdateView SAVE_MAIN_ITEMS_STAGE] Item form {item_form.prefix} has parent_item_ref='{parent_item_form_prefix_ref}', will be processed as EXTRA later.")

            # Stage 3: Process and Save EXTRA items, linking them to their parents
            print(f"[OrderUpdateView SAVE_EXTRA_ITEMS_STAGE] Starting to process and save EXTRA items.")
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
                                print(f"[OrderUpdateView SAVE_EXTRA_ITEMS_STAGE] Linking EXTRA item (form {item_form.prefix}) to PARENT item (form {parent_item_form_prefix_ref}, PK {parent_main_item_instance.pk})")
                            else:
                                print(f"[OrderUpdateView SAVE_EXTRA_ITEMS_STAGE] WARNING: Could not find saved PARENT main item for prefix '{parent_item_form_prefix_ref}' for EXTRA item (form {item_form.prefix}). Parent link will be None.")
                                extra_instance.parent_item = None # Or handle error

                            print(f"[OrderUpdateView SAVE_EXTRA_ITEMS_STAGE] About to save EXTRA OrderItem instance (from form {item_form.prefix}): Menu: {extra_instance.menu_item}, Qty: {extra_instance.quantity}, ParentPK: {extra_instance.parent_item_id if extra_instance.parent_item else 'None'}")
                            extra_instance.save()
                            print(f"[OrderUpdateView SAVE_EXTRA_ITEMS_STAGE] Saved EXTRA OrderItem instance. PK: {extra_instance.pk}")
                            
                            # Decide if it's new or updated based on its own PK status
                            if not item_form.instance.pk or item_form.instance.pk != extra_instance.pk: # if it was a new extra item
                                new_items_info.append(f"{extra_instance.menu_item.name} (Extra)" if extra_instance.menu_item else "Unknown Extra")
                            else: # it was an existing extra item that changed
                                updated_items_info.append(f"{extra_instance.menu_item.name} (Extra)" if extra_instance.menu_item else "Unknown Extra")
                        # If an existing extra item is unchanged, it's already linked (or should be), so no specific action here.
                        # The formset handles existing instances correctly if they don't change.
            
            print("[OrderUpdateView] All item operations (main and extra add/update/delete) supposedly done.")
            
            print("[OrderUpdateView] About to call self.object.save() to update totals.")
            # ... (rest of the logging for items in DB and final Order.save() call remains the same) ...
            current_items_in_db = list(OrderItem.objects.filter(order=self.object))
            print(f"[OrderUpdateView] Items for order {self.object.pk} before final save: {len(current_items_in_db)} items.")
            for item_in_db in current_items_in_db:
                print(f"  - DB Item: {item_in_db.menu_item.name}, Qty: {item_in_db.quantity}, Subtotal: {item_in_db.subtotal}, PK: {item_in_db.pk}, ParentPK: {item_in_db.parent_item_id}")

            self.object.save() 
            print(f"[OrderUpdateView] Final self.object.save() completed. Order total: {self.object.total_price}")
            
            message_parts = [f'Order #{self.object.order_number or self.object.id} updated successfully!']
            if deleted_items_info:
                message_parts.append(f"Removed: {', '.join(deleted_items_info)}")
            if new_items_info:
                message_parts.append(f"Added: {', '.join(new_items_info)}")
            if updated_items_info:
                message_parts.append(f"Updated: {', '.join(updated_items_info)}")
            
            success_msg = " | ".join(message_parts)
            messages.success(self.request, success_msg)
            print(f"[OrderUpdateView] Success message set: {success_msg}")
            print(f"[OrderUpdateView] Redirecting to {self.get_success_url()}")
            return redirect(self.get_success_url())
            
        except Exception as e:
            print(f"[OrderUpdateView] EXCEPTION in form_valid: {type(e).__name__} - {str(e)}")
            import traceback
            traceback.print_exc() 
            messages.error(self.request, f"CRITICAL Error updating order: {str(e)}. Please check logs.")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There were errors in your form. Please check and try again.")
        return self.render_to_response(self.get_context_data(form=form))


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
