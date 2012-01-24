from collections import namedtuple

from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

Generator = namedtuple('Generator', ('url_name', 'title'))
Item = namedtuple('Item', ('href', 'title'))

class Menu:
    def __init__(self):
        self.generators = []
    
    def __getitem__(self, key):
        # g = self.generators[key]
        # return Item(reverse(g.link_name), g.title)
        return self.generators[key]
    
    def append(self, title, url_name):
        self.generators.append(Generator(url_name, title))

class MainMenu(Menu):
    def __init__(self, request):
        Menu.__init__(self)
        self.append("Home", 'front_page')
        
        if request.user.is_authenticated:
            self.append("Documents", 'admin:documents_document_changelist')
            self.append("Users", 'admin:binder_intranetuser_changelist')
        
        if request.user.is_superuser or \
            request.user.groups.filter(name='Manager'): 
            self.append("Admin", 'admin:index')
