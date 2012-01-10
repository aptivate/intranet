from django import template
from django.core.urlresolvers import reverse
from django.utils import html

"""
class MenuItemNode(template.Node):
    def __init__(self, label, link_name):
        if (link_name[0] == link_name[-1] and
            link_name[0] in ('"', "'")):
            # quoted name, means a literal lookup with reverse(),
            # after removing the quotes
            link_name = link_name[1:-1]
        else:
            # unquoted name, means we should get the value from the context
            link_name = template.Variable(link_name)

        self.link_name = link_name

        if (label[0] == label[-1] and label[0] in ('"', "'")):
            # quoted label, means that we should just remove the quotes
            label = label[1:-1]
        else:
            # unquoted label, means that we should get the value from context
            label = template.Variable(label)

        self.label = label
    
    def render(self, context):
        if 'resolve' in self.link_name:
            # need to resolve the variable in context
            href = reverse(self.link_name.resolve(context))
        else:
            href = reverse(self.link_name)

        if 'resolve' in self.label:
            label = self.label.resolve(context)
        else:
            label = self.label

        attributes = {}
        if context.path == href:
            attributes['class'] = 'selected'
        
        attributes = ['%s="%s"' % (html.escape(k), html.escape(v))
            for k, v in attributes.iteritems()]
        attributes = " ".join(attributes)
        
        return '<li %s><a href="%s">%s</a></li>' % (attributes,
            html.escape(href), html.escape(self.label))

@register.tag
def menu_item(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, link_name, label = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires two arguments" %
            token.contents.split()[0])
    
    return MenuItemNode(label, link_name)
"""

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
