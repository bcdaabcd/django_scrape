from django import template
from items.models import Item
from django.http import Http404

register = template.Library()

@register.simple_tag
def fav_status(obj):
    if obj.is_favorite:
        return 'selected'
    else:
        return ''

@register.simple_tag 
def from_where(request):
    url = request.GET.get('from')
    if url:
        return url
    else:
        return "/item/"