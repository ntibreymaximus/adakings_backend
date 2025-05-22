from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    A form for creating new users. Includes all required fields plus
    role selection and other custom fields.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'staff_id')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        
        # Add Bootstrap classes to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'role':
                field.widget.attrs['class'] = 'form-select'  # Use form-select for dropdown
        
        # Add conditional fields based on role
        self.fields['delivery_zone'] = forms.CharField(
            required=False,
            max_length=100,
            help_text=_('Required for delivery staff'),
            widget=forms.TextInput(attrs={'class': 'form-control'})
        )
        self.fields['vehicle_type'] = forms.CharField(
            required=False,
            max_length=50,
            help_text=_('Required for delivery staff'),
            widget=forms.TextInput(attrs={'class': 'form-control'})
        )
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        # Validate delivery-specific fields if role is delivery
        if role == CustomUser.DELIVERY:
            delivery_zone = cleaned_data.get('delivery_zone')
            vehicle_type = cleaned_data.get('vehicle_type')
            
            if not delivery_zone:
                self.add_error('delivery_zone', _('Delivery zone is required for delivery staff'))
                
            if not vehicle_type:
                self.add_error('vehicle_type', _('Vehicle type is required for delivery staff'))
                
        return cleaned_data


class CustomUserChangeForm(UserChangeForm):
    """
    A form for updating users. Includes all fields on the user, but replaces
    the password field with admin's disabled password hash display field.
    """
    password = None  # Don't show password field in the form
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'staff_id')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'role':
                field.widget.attrs['class'] = 'form-select'  # Use form-select for dropdown
        
        # Add conditional fields based on role
        self.fields['delivery_zone'] = forms.CharField(
            required=False,
            max_length=100,
            help_text=_('Required for delivery staff'),
            widget=forms.TextInput(attrs={'class': 'form-control'})
        )
        self.fields['vehicle_type'] = forms.CharField(
            required=False,
            max_length=50,
            help_text=_('Required for delivery staff'),
            widget=forms.TextInput(attrs={'class': 'form-control'})
        )
        
        # Pre-populate delivery fields if they exist
        if self.instance and hasattr(self.instance, 'delivery_zone'):
            self.fields['delivery_zone'].initial = self.instance.delivery_zone
            
        if self.instance and hasattr(self.instance, 'vehicle_type'):
            self.fields['vehicle_type'].initial = self.instance.vehicle_type
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        # Validate delivery-specific fields if role is delivery
        if role == CustomUser.DELIVERY:
            delivery_zone = cleaned_data.get('delivery_zone')
            vehicle_type = cleaned_data.get('vehicle_type')
            
            if not delivery_zone:
                self.add_error('delivery_zone', _('Delivery zone is required for delivery staff'))
                
            if not vehicle_type:
                self.add_error('vehicle_type', _('Vehicle type is required for delivery staff'))
                
        return cleaned_data
