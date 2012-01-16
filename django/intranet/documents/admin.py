# http://www.ibm.com/developerworks/opensource/library/os-django-admin/index.html

from django.contrib import admin
import models

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper

class RelatedFieldWithoutAddLink(RelatedFieldWidgetWrapper):
    def __init__(self, widget, rel, admin_site, can_add_related=None):
        RelatedFieldWidgetWrapper.__init__(self, widget, rel, admin_site,
            can_add_related=False)

from django.forms.models import ModelForm

class DocumentAdminForm(ModelForm):
    class Meta:
        model = models.Document
        # widgets = {'document_type': RelatedFieldWithoutAddLink,}

from django.db import models as django_fields
import django.contrib.admin
from django.forms.util import flatatt as attributes_to_str
from django.utils.safestring import mark_safe

class URLFieldWidgetWithLink(admin.widgets.AdminURLFieldWidget):
    def render(self, name, value, attrs=None):
        html = admin.widgets.AdminURLFieldWidget.render(self, name, value,
            attrs=attrs)

        if value is not None:
            final_attrs = dict(href=value, target='_blank')
            html += " <a %s>(open)</a>" % attributes_to_str(final_attrs)
        
        return mark_safe(html)

from django.forms.widgets import ClearableFileInput, CheckboxInput
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape

class AdminFileWidgetWithSize(admin.widgets.AdminFileWidget):
    template_with_initial = u'%(initial_text)s: %(initial)s (%(size)s) %(clear_template)s<br />%(input_text)s: %(input)s'

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = u'%(input)s'
        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['size'] = filesizeformat(value.size)
            substitutions['initial'] = (u'<a href="%s">%s</a>'
                                        % (escape(value.url),
                                           escape(force_unicode(value))))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions
        
        return mark_safe(template % substitutions)

class DocumentAdmin(admin.ModelAdmin):
    formfield_overrides = {
        django_fields.URLField: {'widget': URLFieldWidgetWithLink},
        django_fields.FileField: {'widget': AdminFileWidgetWithSize},
    }
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        old_formfield = admin.ModelAdmin.formfield_for_dbfield(self, db_field,
            **kwargs)
        if (hasattr(old_formfield, 'widget') and
            isinstance(old_formfield.widget, RelatedFieldWidgetWrapper)):
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

admin.site.register(models.Document, DocumentAdmin)

admin.site.register(models.DocumentType, admin.ModelAdmin)
admin.site.register(models.Program, admin.ModelAdmin)
