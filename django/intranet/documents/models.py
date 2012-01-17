from django.db import models
import binder.models

# http://djangosnippets.org/snippets/1054/

class DocumentType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __unicode__(self):
        return self.name

class Document(models.Model):
    title = models.CharField(max_length=255, unique=True)
    document_type = models.ForeignKey(DocumentType)
    programs = models.ManyToManyField(binder.models.Program)
    file = models.FileField(upload_to='documents', blank=True)
    notes = models.TextField()
    authors = models.ManyToManyField(binder.models.IntranetUser)
    created = models.DateTimeField(auto_now_add = True)
    hyperlink = models.URLField(blank=True)
    
    def __unicode__(self):
        return self.title

    def clean(self):
        models.Model.clean(self)
        
        from django.core.exceptions import ValidationError
        
        if not self.file and not self.hyperlink:
            raise ValidationError('You must either attach a file ' +
                'or provide a hyperlink')
