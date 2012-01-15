# http://www.ibm.com/developerworks/opensource/library/os-django-admin/index.html

from django.contrib import admin
import models

class DocumentAdmin(admin.ModelAdmin):
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
