import re
from django import template
from django.template.defaultfilters import stringfilter
from django.urls import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from songs.models import Song

register = template.Library()

@register.filter
@stringfilter
def spaces(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub(r'\s', '&'+'nbsp;', esc(value)))
spaces.needs_autoescape = True

@register.filter
@stringfilter
def hide_email_address(value):
    def modify_email_address(address):
        return address.replace("@", "_")

    return re.sub(r'([a-zA-Z0-9+._-]+)@([a-zA-Z0-9._-]+)\.([a-zA-Z0-9_-]+)', lambda x: modify_email_address(x.group()), value)

@register.filter(name='modpage')
def modpage(value):
    pattern = r'\[modpage\](\d+)\[/modpage\]'

    def replace_link(match):
        song_id = match.group(1)
        try:
            song = Song.objects.get(id=song_id)
            url = reverse('view_song', kwargs = {'pk': song.id})
            return f'<a href="{url}">{song.get_title()}</a>'
        except Song.DoesNotExist:
            return match.group(0)  # Return the original text if song doesn't exist

    # Use regex to replace [modpage] tags with links
    return re.sub(pattern, replace_link, value)

@register.filter
def url_with_page(querydict, page_number):
    """
    Returns a URL for the given page number in a paginated list.
    """
    querydict = querydict.copy()
    querydict['page'] = page_number
    return querydict.urlencode()
