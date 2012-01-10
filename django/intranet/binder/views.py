# Create your views here.

from django.views.generic.base import TemplateView

import settings

class FrontPageView(TemplateView):
     template_name = 'front_page.dhtml'
     
     def get_context_data(self, **kwargs):
         return settings.GLOBAL_CONTEXT
