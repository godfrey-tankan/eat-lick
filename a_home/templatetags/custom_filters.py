# templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get dictionary item by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def get_attribute(obj, attr):
    """Get object attribute by name"""
    return getattr(obj, attr, None)


@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def get_key(value, key):
    """Alternative to get_item - more reliable"""
    try:
        return value.get(key)
    except (AttributeError, KeyError):
        return None


@register.filter
def to_list(value):
    """Convert to list if possible"""
    if hasattr(value, "__iter__") and not isinstance(value, str):
        return list(value)
    return [value]
