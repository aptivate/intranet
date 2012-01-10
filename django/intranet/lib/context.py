import settings
import binder.main_menu
import lib.dictutils

CONTEXT_GENERATORS = {
    'main_menu_items': binder.main_menu.generate,
    }

GLOBAL_CONTEXT_WITH_MENU = lib.dictutils.GeneratedDict(CONTEXT_GENERATORS,
    settings.GLOBAL_CONTEXT)

def context_with_global(**kwargs):
    """Merge settings.GLOBAL_CONTEXT with a newly generated main menu
    and the provided keyword arguments, to conveniently generate a context
    object to pass to django.contrib.auth"""
    return lib.dictutils.merge(
        {'extra_context': {'global': GLOBAL_CONTEXT_WITH_MENU}},
        kwargs)
