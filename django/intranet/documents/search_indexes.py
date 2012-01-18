import datetime
import docx

from django.db.models import signals
from haystack.indexes import *
from haystack import site
from magic import Magic

from models import Document

class DocumentIndex(RealTimeSearchIndex):
    text = CharField(model_attr='file', document=True)
    title = CharField(model_attr='title')
    notes = CharField(model_attr='notes')
    authors = CharField()
    
    def prepare_authors(self, document):
        # print "authors = %s" % document.authors.all()
        return ', '.join([user.full_name for user in document.authors.all()])
        # return [(user.id, user.full_name) for user in document.authors.all()]
        
    def _setup_save(self, model):
        """Before allowing the model to be saved, we should check that
        we can index the document properly."""
        super(DocumentIndex, self)._setup_save(model)
        signals.pre_save.connect(self.test_object, sender=model)

    def test_object(self, instance, **kwargs):
        """
        Check that we can index a single object. Attached to the class's
        pre-save hook.
        """
        # Check to make sure we want to index this first.
        if self.should_update(instance, **kwargs):
            self.prepare_text(instance)

    def prepare_text(self, document):
        """
        print "file = %s" % dir(document.file)
        print "file.name = %s" % document.file.name
        print "file.path = %s" % document.file.path
        print "file.url = %s" % document.file.url
        print "dir(file.file) = %s" % dir(document.file.file)
        print "file.file.name = %s" % document.file.file.name
        # print "file.file.path = %s" % document.file.file.path
        print "upload_to = %s" % document.file.field.upload_to
        """

        if document.file is not None:
            try:
                document.file.open()
                f = document.file.file
                magic = Magic(mime=True)
                mime = magic.from_buffer(f.read(1024))
                f.seek(0) # reset to beginning
            
                if mime == 'application/zip':
                    # is it a DOCX file?
                    document = docx.opendocx(document.file)
                    paratextlist = docx.getdocumenttext(document)
                    return "\n\n".join(paratextlist)
                else:
                    data = f.read(1<<26) # 64 MB
                    return data
            finally:
                if f is not None:
                    f.close()

site.register(Document, DocumentIndex)