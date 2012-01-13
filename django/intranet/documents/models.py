from django.db import models
from django.contrib.auth.models import User

# http://djangosnippets.org/snippets/1054/

class DocumentType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __unicode__(self):
        return self.name

class Program(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __unicode__(self):
        return self.name

class Document(models.Model):
    title = models.CharField(max_length=255, unique=True)
    document_type = models.ForeignKey(DocumentType)
    programs = models.ManyToManyField(Program)
    file = models.FileField(upload_to='documents')
    notes = models.TextField()
    authors = models.ManyToManyField(User)
    created = models.DateTimeField(auto_now_add = True)
    
    def __unicode__(self):
        return self.title
