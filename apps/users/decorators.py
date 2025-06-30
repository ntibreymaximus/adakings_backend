from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages

def role_required(role, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator factory for views that checks if the user is logged in and has the
    required role, redirecting to the log-in page if necessary.
    """
    def check_role(user):
        return user.is_authenticated and user.role == role
    
    return user_passes_test(check_role, login_url=login_url, redirect_field_name=redirect_field_name)

def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is an admin,
    redirecting to the login page if necessary.
    """
    actual_decorator = role_required(
        role='admin',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def frontdesk_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is frontdesk staff,
    redirecting to the login page if necessary.
    """
    actual_decorator = role_required(
        role='frontdesk',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def kitchen_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is kitchen staff,
    redirecting to the login page if necessary.
    """
    actual_decorator = role_required(
        role='kitchen',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def delivery_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is delivery staff,
    redirecting to the login page if necessary.
    """
    actual_decorator = role_required(
        role='delivery',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def superadmin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is a superadmin,
    redirecting to the login page if necessary.
    """
    actual_decorator = role_required(
        role='superadmin',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def role_required_class(allowed_roles=None):
    """
    Class-based decorator for checking role permissions that can be used with class-based views.
    Usage:
    @method_decorator(role_required_class(['admin', 'frontdesk']), name='dispatch')
    class MyView(View):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:login')
            
            if not allowed_roles or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You don't have permission to access this page.")
            return redirect('users:access_denied')
        
        return _wrapped_view
    
    return decorator

