from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag('hotel_booking/includes/pagination.html')
def pagination(page_obj, request=None):
    """Виджет пагинации"""
    return {
        'page_obj': page_obj,
        'request': request,
    }

@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря"""
    return dictionary.get(key) if dictionary else None

@register.filter
def getattr(obj, attr):
    """Получить атрибут объекта по имени"""
    try:
        return obj.__getattribute__(attr)
    except AttributeError:
        return None