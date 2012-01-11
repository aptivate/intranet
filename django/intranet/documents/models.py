from django.db import models

# http://djangosnippets.org/snippets/1054/

class Document(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add = True)
    author = models.ForeignKey('auth.User')
    file = models.FileField(upload_to='documents')
    
    def __unicode__(self):
        return self.title
