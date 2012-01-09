from django.conf.urls.defaults import patterns, include, url

import django.contrib.auth.views

import combined_settings

import binder.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

global_context = {
    'app_title': combined_settings.APP_TITLE,
}

extra_context = {'global': global_context} 

urlpatterns = patterns('',
    # Examples:
    url(r'^$', binder.views.FrontPageView.as_view(), name='front_page'),
    (r'^login$', django.contrib.auth.views.login,
        {'template_name': 'login.dhtml', 'extra_context': extra_context}),
    # url(r'^intranet/', include('intranet.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

from collections import namedtuple
from django.core.urlresolvers import reverse

MainMenuItem = namedtuple('MainMenuItem', ('href', 'title'))

global_context['main_menu_items'] = [
    MainMenuItem(reverse(django.contrib.auth.views.login), 'Log in'),
]
