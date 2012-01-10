from django.conf.urls.defaults import patterns, include, url

import lib.context
import urls
import documents.views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', documents.views.IndexView.as_view(**lib.context.context_with_global()),
        name='intranet-documents-index'),
)
