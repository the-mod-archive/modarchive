from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
@stringfilter
def spaces(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '&'+'nbsp;', esc(value)))
spaces.needs_autoescape = True

@register.filter
@stringfilter
def hide_email_address(value):
    def modify_email_address(address):
        return address.replace("@", "_")

    return re.sub(r'([a-zA-Z0-9+._-]+)@([a-zA-Z0-9._-]+)\.([a-zA-Z0-9_-]+)', lambda x: modify_email_address(x.group()), value)