import datetime
from haystack.indexes import *
from haystack import site
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

    def prepare_text(self, document):
        print "file = %s" % document.file.file
        if document.file is not None:
            try:
                document.file.open()
                f = document.file.file
                data = f.read(1<<26) # 64 MB
                return data
            finally:
                if f is not None:
                    f.close()

site.register(Document, DocumentIndex)