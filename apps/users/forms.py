"""
Django forms for custom user model
Contains forms for user creation and modification in Django admin
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users in Django admin.
    Extends Django's UserCreationForm to include custom fields.
    """
    
    email = forms.EmailField(
        required=True,
        help_text=_("Required. Enter a valid email address."),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text=_("Optional. User's first name."),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text=_("Optional. User's last name."),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        initial=CustomUser.FRONTDESK,
        help_text=_("User role determines access permissions."),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Delivery-specific fields (shown conditionally)
    delivery_zone = forms.CharField(
        max_length=100,
        required=False,
        help_text=_("Geographic area assigned for deliveries (for delivery staff only)."),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    vehicle_type = forms.CharField(
        max_length=50,
        required=False,
        help_text=_("Type of vehicle used for deliveries (for delivery staff only)."),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name', 
            'role', 'delivery_zone', 'vehicle_type', 
            'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make email required
        self.fields['email'].required = True
        
        # Add helpful text to username field
        self.fields['username'].help_text = _(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        )

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def save(self, commit=True):
        """Save the form and set email"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Form for editing existing users in Django admin.
    Extends Django's UserChangeForm to include custom fields.
    """
    
    email = forms.EmailField(
        required=True,
        help_text=_("Required. Enter a valid email address."),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        help_text=_("User role determines access permissions."),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Delivery-specific fields
    delivery_zone = forms.CharField(
        max_length=100,
        required=False,
        help_text=_("Geographic area assigned for deliveries (for delivery staff only)."),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    vehicle_type = forms.CharField(
        max_length=50,
        required=False,
        help_text=_("Type of vehicle used for deliveries (for delivery staff only)."),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name', 
            'role', 'delivery_zone', 'vehicle_type',
            'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions', 'last_login', 'date_joined'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make email required
        self.fields['email'].required = True
        
        # Make readonly fields non-editable in the form
        if 'last_login' in self.fields:
            self.fields['last_login'].disabled = True
        if 'date_joined' in self.fields:
            self.fields['date_joined'].disabled = True

    def clean_email(self):
        """Validate email uniqueness (excluding current user)"""
        email = self.cleaned_data.get('email')
        if email:
            existing_user = CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def clean(self):
        """Additional validation for role-based requirements"""
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        delivery_zone = cleaned_data.get('delivery_zone')
        vehicle_type = cleaned_data.get('vehicle_type')
        
        # Validate delivery staff fields
        if role == CustomUser.DELIVERY:
            if not delivery_zone:
                self.add_error('delivery_zone', _("Delivery zone is required for delivery staff."))
            if not vehicle_type:
                self.add_error('vehicle_type', _("Vehicle type is required for delivery staff."))
        
        return cleaned_data
