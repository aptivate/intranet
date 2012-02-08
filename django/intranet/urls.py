import django.contrib.auth.views

import settings
import binder.urls
import documents.urls
import search.urls

from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin

# Uncomment the next two lines to enable the admin:

admin.autodiscover()

from django.contrib.auth.models import User
if User in admin.site._registry:
    admin.site.unregister(User)
from django.contrib.sites.models import Site
if Site in admin.site._registry:
    admin.site.unregister(Site)

urlpatterns = patterns('',
    # Examples:
    url(r'', include(binder.urls)),
    url(r'^documents/', include(documents.urls)),
    # url(r'^users/', include(admin.site._registry[User].urls)),
    # url(r'^intranet/', include('intranet.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    # url(r'^search/', include(haystack.urls)),
    url(r'^search/', include(search.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
