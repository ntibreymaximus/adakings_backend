from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem, OrderItemExtra
from apps.menu.models import MenuItem, Extra


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
                'placeholder': 'Customer Name'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+233XXXXXXXXX or 0XXXXXXXXX'
            }),
            'delivery_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleLocationField(this.value)'
            }),
            'delivery_location': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Delivery Address (required for delivery orders)',
                'rows': 3
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Additional order notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default status to Pending for new orders
        if not kwargs.get('instance'):
            self.fields['status'].initial = 'Pending'
        
        # Configure delivery_location field
        self.fields['delivery_location'].required = False
        
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
    """Form for adding menu items to an order"""
    
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity']
        exclude = ['order', 'unit_price', 'subtotal']
        widgets = {
            'menu_item': forms.Select(attrs={
                'class': 'form-select menu-item-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '1', 
                'value': '1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show available menu items
        self.fields['menu_item'].queryset = MenuItem.objects.filter(is_available=True)
        
        # Add data attributes to menu item select for price data
        if self.fields['menu_item'].queryset.exists():
            choices = []
            for item in self.fields['menu_item'].queryset:
                choices.append((
                    item.id, 
                    f"{item.name} (${item.price:.2f})"
                ))
            self.fields['menu_item'].choices = choices
    
    def clean_quantity(self):
        """Ensure quantity is at least 1"""
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise ValidationError("Quantity must be at least 1")
        return quantity


class OrderItemExtraForm(forms.ModelForm):
    """Form for adding extras to an order item"""
    
    class Meta:
        model = OrderItemExtra
        fields = ['extra', 'quantity']
        exclude = ['order_item', 'unit_price', 'subtotal']
        widgets = {
            'extra': forms.Select(attrs={
                'class': 'form-select extra-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '1', 
                'value': '1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show available extras
        self.fields['extra'].queryset = Extra.objects.filter(is_available=True)
        
        # Add data attributes to extra select for price data
        if self.fields['extra'].queryset.exists():
            choices = []
            for item in self.fields['extra'].queryset:
                choices.append((
                    item.id, 
                    f"{item.name} (${item.price:.2f})"
                ))
            self.fields['extra'].choices = choices
    
    def clean_quantity(self):
        """Ensure quantity is at least 1"""
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
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

