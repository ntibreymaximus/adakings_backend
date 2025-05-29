from django import template

register = template.Library()

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

