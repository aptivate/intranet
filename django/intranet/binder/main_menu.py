from collections import namedtuple
from django.core.urlresolvers import reverse

MainMenuItem = namedtuple('MainMenuItem', ('href', 'title'))

def generate():
    return [
        MainMenuItem(reverse('front_page'), 'Home'),
    ]
