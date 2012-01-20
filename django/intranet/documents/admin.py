# http://www.ibm.com/developerworks/opensource/library/os-django-admin/index.html

import models
import binder.admin
import django.contrib.admin

from django.db import models as django_fields
from django.forms.models import ModelForm

class DocumentAdminForm(ModelForm):
    class Meta:
        model = models.Document
        # widgets = {'document_type': RelatedFieldWithoutAddLink,}

class DocumentAdmin(django.contrib.admin.ModelAdmin):
    list_display = ('title', models.Document.get_authors)
    
    formfield_overrides = {
        django_fields.URLField: {'widget': binder.admin.URLFieldWidgetWithLink},
        django_fields.FileField: {'widget': binder.admin.AdminFileWidgetWithSize},
    }
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        old_formfield = django.contrib.admin.ModelAdmin.formfield_for_dbfield(
            self, db_field, **kwargs)
        if (hasattr(old_formfield, 'widget') and
            isinstance(old_formfield.widget, binder.admin.RelatedFieldWidgetWrapper)):
            old_formfield.widget.can_add_related = False
        return old_formfield
    
    """
    def get_form(self, request, obj=None, **kwargs):
        new_args = dict(form=DocumentAdminForm, **kwargs)
        return admin.ModelAdmin.get_form(self, request, obj=obj, **new_args)
    """
    
    def get_urls(self):
        urlpatterns = super(DocumentAdmin, self).get_urls()
        # print "patterns = %s" % urlpatterns
        # print "name = %s" % urlpatterns[0].name
        # print "login template = %s" % admin.sites.site.login_template
        return urlpatterns
    
    """
    def has_add_permission(self, request):
        print "user = %s" % request.user
        opts = self.opts
        perm = opts.app_label + '.' + opts.get_add_permission()
        print "perm = %s" % perm
        print "has_perm = %s" % request.user.has_perm(perm)
        return admin.ModelAdmin.has_add_permission(self, request)
        """

django.contrib.admin.site.register(models.Document, DocumentAdmin)

django.contrib.admin.site.register(models.DocumentType, 
    django.contrib.admin.ModelAdmin)
