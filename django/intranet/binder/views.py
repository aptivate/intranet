# Create your views here.

from django.views.generic.base import TemplateView

import settings
import binder.main_menu

class FrontPageView(TemplateView):
    template_name = 'front_page.dhtml'
    """
    extra_context = {}
    
    def get_context_data(self, **kwargs):
        # print "get_context_data: %s" % str(self.extra_context['global']['main_menu_items'])
        # print "get_context_data: %s" % str(binder.main_menu.generate())
        return self.extra_context
    """
