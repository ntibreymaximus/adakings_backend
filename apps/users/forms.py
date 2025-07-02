"""
Forms for the users app.
Provides custom forms for user creation and modification in Django admin.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form for Django admin.
    Extends the default UserCreationForm to work with CustomUser model.
    """
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    first_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    last_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES, 
        initial=CustomUser.FRONTDESK,
        help_text="Select the user's role in the system."
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'role'
        )

    def save(self, commit=True):
        """
        Save the user with the provided data.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Custom user change form for Django admin.
    Extends the default UserChangeForm to work with CustomUser model.
    """
    delivery_zone = forms.CharField(
        max_length=100, 
        required=False,
        help_text="Delivery zone for delivery staff (optional for other roles)."
    )
    vehicle_type = forms.CharField(
        max_length=50, 
        required=False,
        help_text="Vehicle type for delivery staff (optional for other roles)."
    )

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make delivery fields conditional based on role
        if self.instance and self.instance.role != CustomUser.DELIVERY:
            self.fields['delivery_zone'].widget = forms.HiddenInput()
            self.fields['vehicle_type'].widget = forms.HiddenInput()

    def clean(self):
        """
        Custom validation for the form.
        """
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        # Clear delivery fields if not delivery role
        if role != CustomUser.DELIVERY:
            cleaned_data['delivery_zone'] = ''
            cleaned_data['vehicle_type'] = ''
            
        return cleaned_data
