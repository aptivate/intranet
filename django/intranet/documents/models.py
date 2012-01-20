import binder.models
import django.dispatch

from django.db import models

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

    on_validate = django.dispatch.Signal(providing_args=['instance'])    
    
    def __unicode__(self):
        return "Document<%s>" % self.title
    
    def get_authors(self):
        return ', '.join([u.full_name for u in self.authors.all()])
    get_authors.short_description = 'Authors'

    def clean(self):
        # print "Document.clean starting"
        
        from django.core.exceptions import ValidationError
        # raise ValidationError("early validation error")
        
        models.Model.clean(self)
        
        if not self.file and not self.hyperlink:
            raise ValidationError('You must either attach a file ' +
                'or provide a hyperlink')
        
        try:
            self.on_validate.send(sender=Document, instance=self)
        except ValidationError as e:
            # print "on_validate raised a ValidationError: %s" % e
            raise e
        except Exception as e:
            # print "on_validate raised a generic exception: %s" % e
            raise ValidationError(e)    

        # print "Document.clean finished"
            
    @models.permalink
    def get_absolute_url(self):
        """
        from django.core.urlresolvers import reverse
        url = reverse('admin:documents_document_change', [self.id])
        print "reverse for %s = %s" % (self, url)
        return url
        """
        # return ('admin:documents_document_change', [str(self.id)])
        return ('admin:documents_document_readonly', [str(self.id)])
