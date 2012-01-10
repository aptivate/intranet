from django import template
from django.core.urlresolvers import reverse
from django.utils import html

register = template.Library()
@register.simple_tag(takes_context=True)
def menu_item(context, url_name, label):
    href = reverse(url_name)
    
    attributes = {}
    if context['global']['path'] == href:
        attributes['class'] = 'selected'
    
    attributes = ['%s="%s"' % (html.escape(k), html.escape(v))
        for k, v in attributes.iteritems()]
    attributes = " ".join(attributes)
    
    return '<li %s><a href="%s">%s</a></li>' % (attributes,
        html.escape(href), html.escape(label))
