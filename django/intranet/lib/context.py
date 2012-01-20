# extensions to django.core.context_processors

import settings
import binder.main_menu
import haystack.forms

def intranet_global(request):
    return {
        'global': {
            'app_title': settings.APP_TITLE,
            'path': request.path,
            'main_menu': binder.main_menu.MAIN_MENU,
            'search': haystack.forms.ModelSearchForm(request.GET),
            'admin_media': settings.ADMIN_MEDIA_PREFIX,
        },
        'root_path': '/admin',
    }
