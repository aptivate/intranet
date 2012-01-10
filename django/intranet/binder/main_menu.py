from collections import namedtuple

from django.core.urlresolvers import reverse, NoReverseMatch

Generator = namedtuple('Generator', ('url_name', 'title'))
Item = namedtuple('Item', ('href', 'title'))

class Menu:
    generators = []
    
    def __getitem__(self, key):
        # g = self.generators[key]
        # return Item(reverse(g.link_name), g.title)
        return self.generators[key]
    
    def append(self, title, url_name):
        self.generators.append(Generator(url_name, title))

MAIN_MENU = Menu()
MAIN_MENU.append("Home", 'front_page')
MAIN_MENU.append("Documents", 'org.aptivate.intranet.documents.index')

