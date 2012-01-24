# http://www.ibm.com/developerworks/opensource/library/os-django-admin/index.html

import models
import binder.admin
import django.contrib.admin

from django.core.urlresolvers import reverse
from django.db import models as django_fields
from django.forms.models import ModelForm

class DocumentAdminForm(ModelForm):
    class Meta:
        model = models.Document
        # widgets = {'document_type': RelatedFieldWithoutAddLink,}

from django.contrib.admin.views.main import ChangeList

class ChangeListWithLinksToReadOnlyView(ChangeList):
    def url_for_result(self, result):
        opts = self.model._meta
        info = opts.app_label, opts.module_name
        return reverse('admin:%s_%s_readonly' % info,
            args=[getattr(result, self.pk_attname)])

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

        from django.utils.functional import update_wrapper

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        from django.conf.urls.defaults import url
        from django.utils.encoding import force_unicode

        opts = self.model._meta
        info = opts.app_label, opts.module_name
        extra_context = {
            'read_only': True,
            'title': 'View %s' % force_unicode(opts.verbose_name),
            'change_view': 'admin:%s_%s_change' % info,
        }

        urlpatterns = [url(r'^(.+)/readonly$',
                wrap(self.change_view),
                {'extra_context': extra_context},
                name='%s_%s_readonly' % info)] + urlpatterns

        return urlpatterns
    
    def render_change_form(self, request, context, add=False, change=False,
        form_url='', obj=None):
        """
        This is called right at the end of change_view. It seems like the
        best place to set all fields to read-only if this is a read-only
        view, as the fields have already been calculated and are available
        to us. We shouldn't really muck about with the internals of the
        AdminForm object, but this seems like the cleanest (least invasive)
        solution to making a completely read-only admin form.  
        """
        
        if 'read_only' in context or 'readonly' in request.GET:
            adminForm = context['adminform']
            readonly = []
            for name, options in adminForm.fieldsets:
                readonly.extend(options['fields'])
            adminForm.readonly_fields = readonly
            form_template = 'admin/view_form.html'
        else:
            form_template = None

        context['referrer'] = request.META.get('HTTP_REFERER')

        is_popup = context['is_popup']
        
        context['show_delete_link'] = (not is_popup and
            self.has_delete_permission(request, obj))
         
        """
        return django.contrib.admin.ModelAdmin.render_change_form(self,
            request, context, add=add, change=change, form_url=form_url,
            obj=obj)
        """
        
        # What follows was copied from super.render_change_form and
        # adapted to allow passing in a custom template by making
        # form_template an optional method parameter, defaulting to None
        
        from django.utils.safestring import mark_safe
        from django.contrib.contenttypes.models import ContentType
        from django import template
        from django.shortcuts import render_to_response

        opts = self.model._meta
        app_label = opts.app_label
        ordered_objects = opts.get_ordered_objects()
        context.update({
            'add': add,
            'change': change,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': True, # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': hasattr(self.model, 'get_absolute_url'),
            'ordered_objects': ordered_objects,
            'form_url': mark_safe(form_url),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'root_path': self.admin_site.root_path,
        })
        
        if form_template is None:
            if add and self.add_form_template is not None:
                form_template = self.add_form_template
            else:
                form_template = self.change_form_template
        
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response(form_template or [
            "admin/%s/%s/change_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/change_form.html" % app_label,
            "admin/change_form.html"
        ], context, context_instance=context_instance)
    
    def get_changelist(self, request, **kwargs):
        return ChangeListWithLinksToReadOnlyView
    
    def queryset(self, request):
        if request.user.groups.filter(name='Guest'):
            limit_to_program = request.user.program
        else:
            limit_to_program = None

        qs = super(self.__class__, self).queryset(request)
        
        if limit_to_program:
            return qs.filter(programs=limit_to_program)
        else:
            return qs

django.contrib.admin.site.register(models.Document, DocumentAdmin)

django.contrib.admin.site.register(models.DocumentType, 
    django.contrib.admin.ModelAdmin)
