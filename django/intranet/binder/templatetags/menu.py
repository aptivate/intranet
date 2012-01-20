from django import template
from django.core.urlresolvers import reverse
from django.utils import html

register = template.Library()

@register.simple_tag(takes_context=True)
def menu_item(context, uri_or_name, label):
    if uri_or_name[0] == '/':
        href = uri_or_name
    else:
        href = reverse(uri_or_name)
    
    attributes = {}
    if context['global']['path'] == href:
        attributes['class'] = 'selected'
    
    element = 'td'
    
    attributes = ['%s="%s"' % (html.escape(k), html.escape(v))
        for k, v in attributes.iteritems()]
    attributes = " ".join(attributes)
    
    return '<%s %s><a href="%s">%s</a></%s>' % (element, attributes,
        html.escape(href), html.escape(label), element)
