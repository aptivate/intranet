# https://code.djangoproject.com/ticket/16929

"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from models import UserProfile

# Define an inline admin descriptor for UserProfile model
# which acts a bit like a singleton
import django.contrib.admin.options
class UserProfileInline(django.contrib.admin.options.StackedInline):
    template = 'admin/includes/embedded_fieldset.html'
    model = UserProfile
    fk_name = 'user'
    can_delete = False
    max_num = 1 
    verbose_name_plural = 'profile'

# Define a new User admin
class UserAdminWithProfile(UserAdmin):
    inlines = (UserProfileInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdminWithProfile)
"""

import django.db.models
import models

from django import forms
from django.contrib import admin
from django.forms import ModelForm
from django.forms.util import flatatt as attributes_to_str
from django.forms.widgets import ClearableFileInput, CheckboxInput
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe

# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_protect

# csrf_protect_m = method_decorator(csrf_protect)
# from django.db import transaction
# from models import IntranetUser

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper

class RelatedFieldWithoutAddLink(RelatedFieldWidgetWrapper):
    def __init__(self, widget, rel, admin_site, can_add_related=None):
        RelatedFieldWidgetWrapper.__init__(self, widget, rel, admin_site,
            can_add_related=False)

class AdminFileWidgetWithSize(admin.widgets.AdminFileWidget):
    template_with_initial = u'%(initial_text)s: %(initial)s (%(size)s) %(clear_template)s<br />%(input_text)s: %(input)s'
    readonly_template = u'%(initial)s (%(size)s)'
    has_readonly_view = True

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
        
        if attrs.get('readonly'):
            template = self.readonly_template
        
        return mark_safe(template % substitutions)

class URLFieldWidgetWithLink(admin.widgets.AdminURLFieldWidget):
    def render(self, name, value, attrs=None):
        html = admin.widgets.AdminURLFieldWidget.render(self, name, value,
            attrs=attrs)

        if value is not None:
            final_attrs = dict(href=value, target='_blank')
            html += " <a %s>(open)</a>" % attributes_to_str(final_attrs)
        
        return mark_safe(html)

class IntranetUserForm(ModelForm):
    class Meta:
        model = models.IntranetUser
    
    password1 = forms.CharField(required=False, label="New password")
    password2 = forms.CharField(required=False, label="Confirm new password")
    
    COMPLETE_BOTH = 'You must complete both password boxes to set or ' + \
        'change the password'
    
    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        from django.core.exceptions import ValidationError
        
        if password2 and not password1:
            raise ValidationError({'password1': [self.COMPLETE_BOTH]})

        if password1 and not password2:
            raise ValidationError({'password2': [self.COMPLETE_BOTH]})
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError({'password2': ['Please enter ' +
                    'the same password in both boxes.']})
        
        return ModelForm.clean(self)

    def _post_clean(self):
        ModelForm._post_clean(self)

        # because password is excluded from the form, it's not updated
        # in the model instance, so it's never changed unless we poke it
        # in here.
        
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2:
            if password1 == password2:
                self.instance.set_password(password1)

class IntranetUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'job_title', 'program',
        models.IntranetUser.get_userlevel)

    exclude = ['password', 'first_name', 'last_name', 'user_permissions']
    form = IntranetUserForm

    formfield_overrides = {
        django.db.models.URLField: {'widget': URLFieldWidgetWithLink},
        django.db.models.FileField: {'widget': AdminFileWidgetWithSize},
        django.db.models.ImageField: {'widget': AdminFileWidgetWithSize},
    }
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        old_formfield = admin.ModelAdmin.formfield_for_dbfield(self,
            db_field, **kwargs)
        if (hasattr(old_formfield, 'widget') and
            isinstance(old_formfield.widget, RelatedFieldWidgetWrapper)):
            old_formfield.widget.can_add_related = False
        return old_formfield
    
    def get_form(self, request, obj=None, **kwargs):
        result = admin.ModelAdmin.get_form(self, request, obj=obj, **kwargs)
        # print 'get_form => %s' % dir(result)
        # print 'declared_fields => %s' % result.declared_fields
        # print 'base_fields => %s' % result.base_fields
        return result

admin.site.register(models.IntranetUser, IntranetUserAdmin)
admin.site.register(models.Program, admin.ModelAdmin)

from django.contrib.admin.helpers import AdminReadonlyField

class CustomAdminReadOnlyField(AdminReadonlyField):
    """
    Allow widgets that support a custom read-only view to declare it,
    by implementing a has_readonly_view attribute, and responding to
    their render() method differently if readonly=True is passed to it.
    """
    
    def contents(self):
        form = self.form
        field = self.field['field']
        if hasattr(form[field].field.widget, 'has_readonly_view'):
            return form[field].as_widget(attrs={'readonly': True})
        else:
            return AdminReadonlyField.contents(self)