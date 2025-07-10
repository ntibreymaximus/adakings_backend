from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
import json


def log_create(user, obj, request=None, extra_data=None):
    """Log creation of an object."""
    changes = {'created': True}
    if extra_data:
        changes.update(extra_data)
    
    return AuditLog.log_action(
        user=user,
        action=AuditLog.ACTION_CREATE,
        obj=obj,
        changes=changes,
        request=request
    )


def log_update(user, obj, old_values=None, new_values=None, request=None):
    """
    Log update of an object.
    
    Args:
        user: User who made the update
        obj: Object being updated
        old_values: Dict of field names to old values
        new_values: Dict of field names to new values
        request: HttpRequest object
    """
    changes = {}
    
    if old_values and new_values:
        # Calculate what changed
        for field, new_value in new_values.items():
            old_value = old_values.get(field)
            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }
    elif new_values:
        changes = {'updated_fields': list(new_values.keys())}
    
    return AuditLog.log_action(
        user=user,
        action=AuditLog.ACTION_UPDATE,
        obj=obj,
        changes=changes,
        request=request
    )


def log_delete(user, obj, request=None):
    """Log deletion of an object."""
    # Store object details before deletion
    obj_data = {
        'model': obj.__class__.__name__,
        'pk': obj.pk,
        'repr': str(obj)
    }
    
    # Try to serialize important fields
    if hasattr(obj, 'name'):
        obj_data['name'] = obj.name
    if hasattr(obj, 'title'):
        obj_data['title'] = obj.title
    
    return AuditLog.log_action(
        user=user,
        action=AuditLog.ACTION_DELETE,
        obj=obj,
        changes={'deleted_object': obj_data},
        request=request
    )


def log_status_change(user, obj, old_status, new_status, request=None, extra_data=None):
    """Log status change of an object."""
    changes = {
        'status': {
            'old': str(old_status),
            'new': str(new_status)
        }
    }
    if extra_data:
        changes.update(extra_data)
    
    return AuditLog.log_action(
        user=user,
        action=AuditLog.ACTION_STATUS_CHANGE,
        obj=obj,
        changes=changes,
        request=request
    )


def log_payment(user, payment_obj, amount, payment_method, request=None, extra_data=None):
    """Log payment processing."""
    changes = {
        'amount': str(amount),
        'payment_method': payment_method,
        'processed': True
    }
    if extra_data:
        changes.update(extra_data)
    
    return AuditLog.log_action(
        user=user,
        action=AuditLog.ACTION_PAYMENT,
        obj=payment_obj,
        changes=changes,
        request=request
    )


def log_refund(user, payment_obj, amount, reason=None, request=None):
    """Log refund processing."""
    changes = {
        'refund_amount': str(amount),
        'refunded': True
    }
    if reason:
        changes['reason'] = reason
    
    return AuditLog.log_action(
        user=user,
        action=AuditLog.ACTION_REFUND,
        obj=payment_obj,
        changes=changes,
        request=request
    )


def log_toggle(user, obj, field_name, old_value, new_value, request=None):
    """Log toggling of a boolean field."""
    changes = {
        field_name: {
            'old': bool(old_value),
            'new': bool(new_value)
        }
    }
    
    return AuditLog.log_action(
        user=user,
        action=AuditLog.ACTION_TOGGLE,
        obj=obj,
        changes=changes,
        request=request
    )


def get_model_changes(instance, update_fields=None):
    """
    Get changes made to a model instance.
    
    Args:
        instance: Model instance with changes
        update_fields: List of fields that were updated
    
    Returns:
        Dict of field_name: {'old': old_value, 'new': new_value}
    """
    if not hasattr(instance, 'pk') or not instance.pk:
        return {}
    
    # Get the original instance from database
    original = instance.__class__.objects.get(pk=instance.pk)
    changes = {}
    
    # If update_fields is provided, only check those
    fields_to_check = update_fields if update_fields else [f.name for f in instance._meta.fields]
    
    for field_name in fields_to_check:
        original_value = getattr(original, field_name)
        new_value = getattr(instance, field_name)
        
        if original_value != new_value:
            changes[field_name] = {
                'old': str(original_value),
                'new': str(new_value)
            }
    
    return changes


def get_data_changes(old_data, new_data):
    """
    Compare two dictionaries (e.g., serializer data) and return changes.
    
    Args:
        old_data: Dict of original data
        new_data: Dict of new data
    
    Returns:
        Dict of field_name: {'old': old_value, 'new': new_value}
    """
    changes = {}
    
    # Check all fields in new_data
    for field_name, new_value in new_data.items():
        old_value = old_data.get(field_name)
        
        # Convert values to strings for comparison
        old_str = str(old_value) if old_value is not None else 'None'
        new_str = str(new_value) if new_value is not None else 'None'
        
        if old_str != new_str:
            changes[field_name] = {
                'old': old_str,
                'new': new_str
            }
    
    return changes


def get_user_recent_activity(user, limit=10):
    """Get recent activity for a specific user."""
    return AuditLog.objects.filter(user=user).select_related('content_type')[:limit]


def get_object_history(obj, limit=None):
    """Get audit history for a specific object."""
    content_type = ContentType.objects.get_for_model(obj)
    queryset = AuditLog.objects.filter(
        content_type=content_type,
        object_id=obj.pk
    ).select_related('user')
    
    if limit:
        queryset = queryset[:limit]
    
    return queryset
