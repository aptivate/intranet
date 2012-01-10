from django.conf.urls.defaults import patterns, include, url

import django.contrib.auth.views

import settings

import binder.views
import binder.main_menu

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

def merge(*args):
    """Merge the contents of any number of dicts into a single dict. Later
    dicts override earlier ones when their keys overlap."""
    result = {}
    for dict in args:
        result.update(dict)
    return result

class GeneratedDict(object):
    def __init__(self, generators, statics):
        self._generators = generators
        self._statics = statics 
        
    def __contains__(self, key):
        if key in self._generators:
            return True
        else:
            return self._statics.__contains__(key)
    
    def __getitem__(self, key):
        if key in self._generators:
            return self._generators[key]()
        else:
            return self._statics.__getitem__(key)
        
    def __setitem__(self, key, value):
        if key in self._generators:
            raise AttributeError("Cannot assign to a generated key")
        else:
            return self._statics.__setitem__(key, value)

    def __delitem__(self, key):
        if key in self._generators:
            raise AttributeError("Cannot delete a generated key")
        else:
            return self._statics.__delitem__(key)

    def keys(self):
        keys = set(self._generators.keys())
        keys.update(self._statics.keys())
        return keys
    
CONTEXT_GENERATORS = {
    'main_menu_items': binder.main_menu.generate,
    }

GLOBAL_CONTEXT_WITH_MENU = GeneratedDict(CONTEXT_GENERATORS,
    settings.GLOBAL_CONTEXT)

def context_with_global(**kwargs):
    """Merge settings.GLOBAL_CONTEXT with a newly generated main menu
    and the provided keyword arguments, to conveniently generate a context
    object to pass to django.contrib.auth"""
    return merge({'extra_context': {'global': GLOBAL_CONTEXT_WITH_MENU}},
        kwargs)

urlpatterns = patterns('',
    # Examples:
    url(r'^$', binder.views.FrontPageView.as_view(**context_with_global()),
        name='front_page'),
    url(r'^login$', django.contrib.auth.views.login,
        context_with_global(template_name='login.dhtml'), name="login"),
    url(r'^logout$', django.contrib.auth.views.logout,
        context_with_global(template_name='front_page.dhtml'), name="logout"),
    # url(r'^intranet/', include('intranet.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
