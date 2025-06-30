from rest_framework.permissions import BasePermission

class IsStaffUser(BasePermission):
    """
    Allows access only to staff users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsAdminOrFrontdesk(BasePermission):
    """
    Allows access only to users with 'superadmin', 'admin' or 'frontdesk' role.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role in ['superadmin', 'admin', 'frontdesk']
        )


class IsAdminOrFrontdeskNoDelete(BasePermission):
    """
    Allows access to users with 'superadmin', 'admin' or 'frontdesk' role.
    Superadmins have full access including delete. Admins and frontdesk users can view and update but cannot delete.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Superadmins have unrestricted access (including delete)
        if request.user.is_superuser and hasattr(request.user, 'role') and request.user.role == 'superadmin':
            return True
        
        # For delete operations, only superadmins are allowed
        if request.method == 'DELETE':
            return False
        
        # Admin and frontdesk users can view and update
        if hasattr(request.user, 'role') and request.user.role in ['admin', 'frontdesk']:
            return True
        
        return False


class IsAdminOrSuperuser(BasePermission):
    """
    Allows access only to superadmin or admin role users.
    Used for sensitive operations like refunds that should not be available to frontdesk staff.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Allow superadmin users (who are also superusers)
        if request.user.is_superuser and hasattr(request.user, 'role') and request.user.role == 'superadmin':
            return True
        
        # Allow admin role users
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        return False


class IsSuperadminOnly(BasePermission):
    """
    Allows access only to superadmin role users (who are also superusers).
    Used for operations that only superadmins should perform.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser and
            hasattr(request.user, 'role') and 
            request.user.role == 'superadmin'
        )

