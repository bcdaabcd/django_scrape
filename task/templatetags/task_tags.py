from django import template


register = template.Library()

@register.simple_tag
def task_status(obj):
    if obj.enabled == True:
        return 'on'
    else:
        return 'stop'

