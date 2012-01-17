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
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_protect

# csrf_protect_m = method_decorator(csrf_protect)
# from django.db import transaction
# from models import IntranetUser

class IntranetUserForm(ModelForm):
    class Meta:
        model = models.IntranetUser
    
    password1 = forms.CharField(required=False, label="New password")
    password2 = forms.CharField(required=False, label="Confirm new password")
    
    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 == password2:
            self.cleaned_data['password'] = \
                self.instance.hash_password(password1)
        return ModelForm.clean(self)

class IntranetUserAdmin(admin.ModelAdmin):
    exclude = ['password', 'first_name', 'last_name']
    form = IntranetUserForm
    
    def get_form(self, request, obj=None, **kwargs):
        result = admin.ModelAdmin.get_form(self, request, obj=obj, **kwargs)
        print 'get_form => %s' % dir(result)
        print 'declared_fields => %s' % result.declared_fields
        print 'base_fields => %s' % result.base_fields
        return result

admin.site.register(models.IntranetUser, IntranetUserAdmin)
