# http://www.ibm.com/developerworks/opensource/library/os-django-admin/index.html

from django.contrib import admin
import models

class DocumentAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Document, DocumentAdmin)
