from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    """
    Custom admin class for CustomUser model with role-based fields
    and enhanced user management capabilities.
    """
    # Forms to use for add and change
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    # Fields shown in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'staff_id', 
                    'role', 'is_active', 'date_joined')
    
    # Filters in the right sidebar
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    
    # Search functionality
    search_fields = ('username', 'email', 'first_name', 'last_name', 'staff_id')
    
    # Order users by
    ordering = ('-date_joined',)
    
    # Fields organization for the detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Role & Identification'), {'fields': ('role', 'staff_id')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields shown when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'staff_id'),
        }),
        (_('Personal info'), {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name'),
        }),
        (_('Permissions'), {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """
        Dynamically adjust fieldsets based on the user's role.
        Add role-specific fields for delivery staff.
        """
        fieldsets = super().get_fieldsets(request, obj)
        
        # For existing users with delivery role, add delivery-specific fields
        if obj and obj.role == CustomUser.DELIVERY:
            # Convert fieldsets to list for manipulation
            fieldsets = list(fieldsets)
            # Add delivery fields section
            fieldsets.insert(3, (_('Delivery Information'), {'fields': ('delivery_zone', 'vehicle_type')}))
            
        return fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Dynamically adjust the form to include delivery-specific fields 
        when editing a delivery staff member.
        """
        form = super().get_form(request, obj, **kwargs)
        
        # For delivery staff, ensure fields are in the form
        if obj and obj.role == CustomUser.DELIVERY:
            if 'delivery_zone' not in form.base_fields:
                form.base_fields['delivery_zone'] = CustomUserChangeForm.base_fields['delivery_zone']
            if 'vehicle_type' not in form.base_fields:
                form.base_fields['vehicle_type'] = CustomUserChangeForm.base_fields['vehicle_type']
                
        return form

# Register the model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)
