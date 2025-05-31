from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        # Attempt to convert both value and arg to Decimal for precise arithmetic
        decimal_value = Decimal(str(value))
        decimal_arg = Decimal(str(arg))
        return decimal_value - decimal_arg
    except (ValueError, TypeError, InvalidOperation):
        # Fallback if conversion fails, or if types are incompatible
        # You might want to log this error or handle it differently
        try:
            # Try direct subtraction if they are numbers but not Decimal-compatible initially
            return value - arg
        except (ValueError, TypeError):
            # If all else fails, return an empty string or the original value,
            # or raise an error if strictness is required.
            # Returning empty string might hide issues, but avoids template crashing.
            return ''

@register.filter(name='replace')
def replace_string(value, args):
    """
    Replaces occurrences of 'old' with 'new' in 'value'.
    'args' should be a string in the format "old,new".
    Example: {{ my_string|replace:"_, " }} for replacing underscore with space.
    """
    if not isinstance(value, str):
        value = str(value) # Ensure value is a string
    
    if not isinstance(args, str):
        # If args is not a string, it's an invalid usage, return original value
        return value
    
    try:
        old_substring, new_substring = args.split(',', 1)
        return value.replace(old_substring, new_substring)
    except ValueError:
        # This occurs if 'args' does not contain a comma, meaning it's not in "old,new" format.
        # Return the original value or handle as an error, depending on desired strictness.
        return value

