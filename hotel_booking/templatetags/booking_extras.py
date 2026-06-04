from django import template
from datetime import date

register = template.Library()

@register.filter
def days_between(date1, date2):
    """Возвращает количество дней между двумя датами"""
    if date1 and date2:
        delta = date2 - date1
        return delta.days
    return 0

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Вычитает аргумент из значения"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0