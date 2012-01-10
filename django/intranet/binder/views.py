# Create your views here.

from django.views.generic.base import TemplateView

class FrontPageView(TemplateView):
    template_name = 'front_page.dhtml'
    extra_context = {}
    
    def get_context_data(self, **kwargs):
        return self.extra_context
