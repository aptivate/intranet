import django.contrib.auth.views

import settings
import lib.dictutils
import haystack.urls
import binder.views
import documents.urls

from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.static import static
from django.contrib.auth.models import User
from django.contrib import admin

# Uncomment the next two lines to enable the admin:

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 
        binder.views.FrontPageView.as_view(),
        name='front_page'),
    url(r'^login$', django.contrib.auth.views.login,
        {'template_name': 'admin/login.html'}, 
        name="login"),
    url(r'^logout$', django.contrib.auth.views.logout,
        {'template_name': 'front_page.dhtml'}, 
        name="logout"),
    url(r'^documents/', include(documents.urls)),
    url(r'^users/', include(admin.site._registry[User].urls)),
    # url(r'^intranet/', include('intranet.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', include(haystack.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

