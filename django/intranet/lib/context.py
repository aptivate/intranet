# extensions to django.core.context_processors

import settings
import binder.main_menu
import binder.search

def intranet_global(request):
    return {
        'global': {
            'app_title': settings.APP_TITLE,
            'path': request.path,
            'main_menu': binder.main_menu.MainMenu(request),
            'search': binder.search.SearchFormWithAllFields(request.GET),
            'admin_media': settings.ADMIN_MEDIA_PREFIX,
            'user': request.user,
        },
        'root_path': '/admin',
    }
