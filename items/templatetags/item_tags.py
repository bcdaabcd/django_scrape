from django import template
from items.models import Item

register = template.Library()

@register.simple_tag
def fav_status(obj):
    if obj.is_favorite:
        return 'selected'
    else:
        return ''
    
