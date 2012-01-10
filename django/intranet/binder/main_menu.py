from collections import namedtuple
from django.core.urlresolvers import reverse, NoReverseMatch
import settings

Item = namedtuple('Item', ('href', 'title'))

Generator = namedtuple('Generator', ('link_name', 'title'))

def generate():
    items = []
    
    for g in settings.MENU_GENERATORS:
        try:
            items.append(Item(reverse(g.link_name), g.title))
        except NoReverseMatch:
            raise ValueError(("Failed to find a URL named %s. " +
                "Did you install it in urls.py?") % g.link_name)
    
    return items

def append(link_name, title):
    settings.MENU_GENERATORS.append(Generator(link_name, title))