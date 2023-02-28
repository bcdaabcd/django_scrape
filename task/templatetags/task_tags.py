from django import template
import json

register = template.Library()

@register.simple_tag
def task_status(obj):
    if obj.enabled == True:
        return 'on'
    else:
        return 'stop'

@register.simple_tag
def is_price_lower_than(obj):
    if json.loads(obj.kwargs)['email when'] != 'when price lower than':
        return 'hidden'
    else:
        return ''
