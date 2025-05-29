from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from apps.menu.models import MenuItem


class OrderForm(forms.ModelForm):
    """Form for creating and updating orders with customer information"""
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'delivery_type', 'delivery_location',
            'status', 'notes'
        ]
        exclude = ['total_price', 'created_at', 'updated_at']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': "Enter customer's full name"
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+233XXXXXXXXX or 0XXXXXXXXX'
            }),
            'delivery_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleLocationField(this.value)'
            }),
            # delivery_location will now use default Select widget due to model choices
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Additional order notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance or not self.instance.pk:  # For new forms
            self.initial['customer_name'] = ''
            self.initial['customer_phone'] = ''
            
        # Set default status to Pending for new orders
        if not kwargs.get('instance'):
            self.fields['status'].initial = 'Pending'
        
        # Configure delivery_location field
        if 'delivery_location' in self.fields:
            self.fields['delivery_location'].widget.attrs.update({'class': 'form-select'})
            # Ensure it's not required if delivery_type isn't 'Delivery'
            # This is handled by model's blank=True and form's clean method, 
            # but explicitly setting here can be clearer.
            if self.initial.get('delivery_type') != 'Delivery' and not (self.data and self.data.get('delivery_type') == 'Delivery'):
                 self.fields['delivery_location'].required = False
            else: # If it is a delivery, it should be required by the form
                 self.fields['delivery_location'].required = True
        
        # Add help text for phone number field
        self.fields['customer_phone'].help_text = "Enter a valid Ghanaian phone number"
    
    def clean(self):
        """Validate that location is provided for delivery orders"""
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        delivery_location = cleaned_data.get('delivery_location')
        
        if delivery_type == 'Delivery' and not delivery_location:
            self.add_error('delivery_location', 'Location is required for delivery orders')
            
        return cleaned_data


class OrderItemForm(forms.ModelForm):
    """Form for adding items to an order"""
    
    # Add price_display as a non-model field
    price_display = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control item-price',
            'readonly': True,
            'step': '0.01',
            'data-price-type': 'display',
            'style': 'padding-left: 24px;'  # Add space for currency symbol
        })
    )
    
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'unit_price', 'parent_item'] # Added 'parent_item'
        exclude = ['order', 'subtotal'] # 'subtotal' is calculated, 'order' is set by formset
        widgets = {
            'menu_item': forms.Select(attrs={
                'class': 'form-select menu-item-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '1', 
                'value': '1'
            }),
            'unit_price': forms.HiddenInput(attrs={
                'class': 'unit-price-input'
            }),
            'parent_item': forms.HiddenInput(), # Added widget for parent_item
        }
    
    def __init__(self, *args, **kwargs):
        item_type_filter = kwargs.pop('item_type_filter', None) 
        super().__init__(*args, **kwargs)
        
        # --- Logic for existing item instance (price display, original values) ---
        current_menu_item_instance_qs = MenuItem.objects.none() # Queryset for current item if instance exists
        if self.instance and self.instance.pk and self.instance.menu_item:
            current_menu_item_instance_qs = MenuItem.objects.filter(pk=self.instance.menu_item.pk)
            
            initial_price = self.instance.unit_price
            self.initial.update({
                'unit_price': initial_price,
                'price_display': initial_price,
            })
            self.original_menu_item_id = self.instance.menu_item_id
            self.original_unit_price = initial_price
            self.fields['menu_item'].widget.attrs.update({
                'data-original-value': str(self.instance.menu_item.id),
                'data-original-price': str(initial_price)
            })
            self.fields['price_display'].widget.attrs.update({
                'data-original-price': str(initial_price),
                'value': str(initial_price)
            })
            self.fields['unit_price'].initial = initial_price
        else: # New item form
            self.initial.update({
                'unit_price': None,
                'price_display': None,
            })
            self.original_menu_item_id = None
            self.original_unit_price = None

        # --- Set the VALIDATION queryset ---
        # This queryset includes ALL available MenuItems (regular and extras) 
        # plus the current item if the form is bound to an instance.
        # This ensures that any valid MenuItem submitted can pass validation.
        all_available_menu_items_qs = MenuItem.objects.filter(is_available=True)
        self.fields['menu_item'].queryset = (all_available_menu_items_qs | current_menu_item_instance_qs).distinct()

        # --- Build DISPLAY choices based on the item_type_filter ---
        # This controls what the user initially sees in the dropdown.
        choices_list_for_display = []
        
        if item_type_filter == 'regular':
            # Display only 'regular' items in the dropdown.
            # Query from all_available_menu_items_qs which already respects is_available=True.
            regular_items_for_display_qs = all_available_menu_items_qs.filter(item_type='regular')
            regular_choices_tuples = [(item.id, f"{item.name} (₵{item.price:.2f})") for item in regular_items_for_display_qs]
            if regular_choices_tuples:
                choices_list_for_display.append(('Regular Items', regular_choices_tuples))
        elif item_type_filter == 'extra':
            # Display only 'extra' items in the dropdown.
            extra_items_for_display_qs = all_available_menu_items_qs.filter(item_type='extra')
            extra_choices_tuples = [(item.id, f"{item.name} (₵{item.price:.2f})") for item in extra_items_for_display_qs]
            if extra_choices_tuples:
                choices_list_for_display.append(('Extras', extra_choices_tuples))
        else: # 'all' or None (default display logic, e.g., for OrderUpdateView)
            # Display 'Regular Menu Items' group.
            regular_items_for_display_qs = all_available_menu_items_qs.filter(item_type='regular')
            regular_choices_tuples = [(item.id, f"{item.name} (₵{item.price:.2f})") for item in regular_items_for_display_qs]
            if regular_choices_tuples:
                choices_list_for_display.append(('Regular Menu Items', regular_choices_tuples))
            
            # If the current instance's item is an 'extra', it might not be in the 'Regular Menu Items' group.
            # The validation queryset ensures it's valid if submitted.
            # For display on update forms, it will be handled by the next block ensuring current selection is visible.

        # --- Ensure current selection is always in display choices if form is bound to an instance ---
        if self.instance and self.instance.pk and self.instance.menu_item:
            current_selection_obj = self.instance.menu_item
            
            # Check if the current selection is already among the display choices
            current_selection_already_in_display = False
            for group_name, items_in_group in choices_list_for_display:
                if any(item_id == current_selection_obj.id for item_id, item_label in items_in_group):
                    current_selection_already_in_display = True
                    break
            
            if not current_selection_already_in_display:
                # If not present, add it to an appropriate group or a new one.
                current_selection_tuple = (current_selection_obj.id, f"{current_selection_obj.name} (₵{current_selection_obj.price:.2f})")
                group_name_for_current = "Extras" if current_selection_obj.item_type == 'extra' else "Regular Items"
                
                added_to_group = False
                for i, (g_name, g_items) in enumerate(choices_list_for_display):
                    if g_name == group_name_for_current:
                        # Add to existing group
                        choices_list_for_display[i] = (g_name, g_items + [current_selection_tuple])
                        added_to_group = True
                        break
                if not added_to_group:
                    # Create new group for it
                    choices_list_for_display.append((group_name_for_current, [current_selection_tuple]))

        self.fields['menu_item'].choices = choices_list_for_display if choices_list_for_display else [('', '---------')]
        self.fields['parent_item'].required = False # Extras won't always have a parent.
    
    def clean(self):
        """Handle unit price updates when menu item changes"""
        cleaned_data = super().clean()
        menu_item = cleaned_data.get('menu_item')
        
        if menu_item:
            if self.instance and self.instance.pk:
                # For existing items, preserve price if menu item hasn't changed
                if menu_item.id == self.original_menu_item_id:
                    cleaned_data['unit_price'] = self.original_unit_price
                    cleaned_data['price_display'] = self.original_unit_price
                else:
                    # Menu item changed, use new price
                    cleaned_data['unit_price'] = menu_item.price
                    cleaned_data['price_display'] = menu_item.price
            else:
                # New item, use menu item's current price
                cleaned_data['unit_price'] = menu_item.price
                cleaned_data['price_display'] = menu_item.price
        
        return cleaned_data
    
    def clean_quantity(self):
        """Ensure quantity is at least 1"""
        quantity = self.cleaned_data.get('quantity')
        if quantity is None or quantity < 1:
            raise ValidationError("Quantity must be at least 1")
        return quantity




# Form for creating an entire order with multiple items
class OrderWithItemsForm:
    """
    Container for order form with multiple item formsets
    This is not a Django form but a helper class to manage 
    the order form and its related formsets
    """
    
    def __init__(self, *args, **kwargs):
        self.order_form = OrderForm(*args, **kwargs)

