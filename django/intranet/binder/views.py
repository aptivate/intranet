# Create your views here.

from django.views.generic.base import TemplateView

import combined_settings

class FrontPageView(TemplateView):
     template_name = 'front_page.dhtml'
     
     def get_context_data(self, **kwargs):
        return {'APP_TITLE': combined_settings.APP_TITLE}