# Create your views here.

from django.views.generic.base import TemplateView

import settings
import binder.main_menu

class IndexView(TemplateView):
    template_name = 'index.dhtml'
    
    """
    extra_context = {}
    
    def get_context_data(self, **kwargs):
        # print "get_context_data: %s" % str(self.extra_context)
        # print "get_context_data: %s" % str(settings.MENU_GENERATORS)
        # print "get_context_data: %s" % str(binder.main_menu.generate())
        return self.extra_context
    """
