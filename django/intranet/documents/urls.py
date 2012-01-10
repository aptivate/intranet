from django.conf.urls.defaults import patterns, include, url

import documents.views

NAME_PREFIX = 'org.aptivate.intranet.documents.'

urlpatterns = patterns('',
    # Examples:
    url(r'^$', documents.views.IndexView.as_view(),
        name=NAME_PREFIX + "index"),
)
