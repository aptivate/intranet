# extensions to django.core.context_processors

import settings
import binder.main_menu

def intranet_global(request):
    return {
        'global': {
            'app_title': settings.APP_TITLE,
            'path': request.path,
            'main_menu': binder.main_menu.MAIN_MENU,
        },
        'root_path': '/admin',
    }
