import datetime
import docx
import subprocess
import os

from django.db.models import signals
from django.core.files.uploadedfile import TemporaryUploadedFile, \
    InMemoryUploadedFile
from haystack import indexes
from haystack.fields import *
# from haystack import site
from magic import Magic
from StringIO import StringIO
from zipfile import ZipFile

from models import Document

from pdfminer.pdfparser import PDFDocument, PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.layout import LTContainer, LTText, LTTextBox

class TextConverterWithoutPageBreaks(TextConverter):
    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            elif isinstance(item, LTText):
                self.write_text(item.get_text())
            if isinstance(item, LTTextBox):
                self.write_text('\n')
        render(ltpage)
        return

class DocumentIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = CharField(model_attr='file', document=True)
    title = CharField(model_attr='title')
    notes = CharField(model_attr='notes')
    authors = CharField()
    programs = MultiValueField()
    document_type = IntegerField(model_attr='document_type__id')
    
    def get_model(self):
        return Document
    
    def prepare_programs(self, document):
        return [p.id for p in document.programs.all()]

    def prepare_authors(self, document):
        # print "authors = %s" % document.authors.all()
        return ', '.join([user.full_name for user in document.authors.all()])
        # return [(user.id, user.full_name) for user in document.authors.all()]
        
    def _setup_save(self):
        """Before allowing the model to be saved, we should check that
        we can index the document properly."""
        super(DocumentIndex, self)._setup_save()
        """
        signals.pre_save.connect(self.test_object, sender=model,
            dispatch_uid="document_index_on_validate_document")
        """
        Document.on_validate.connect(self.test_object, sender=self.get_model(),
            dispatch_uid="document_index_on_validate_document")

    def test_object(self, instance, **kwargs):
        """
        Check that we can index a single object. Attached to the class's
        pre-save hook.
        """
        # Check to make sure we want to index this first.
        if self.should_update(instance, **kwargs):
            try:
                self.prepare_text(instance)
            except Exception as e:
                from django.core.exceptions import ValidationError
                raise ValidationError({'file': e})

    def safe_popen(self, cmd_with_args, *additional_args):
        cmd_with_args.extend(additional_args)
        
        try:
            return subprocess.Popen(cmd_with_args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        except (OSError, IOError) as e:
            raise Exception('%s: %s' % (cmd_with_args, e))
    
    def ensure_saved(self, file):
        """This may create a temporary file, which will be deleted when
        it's closed, so always close() it but only when you've finished!"""
        
        if isinstance(file, InMemoryUploadedFile):
            print "Writing %s to disk (%d bytes)" % (file, file.size)
            tmp = TemporaryUploadedFile(name=file.name,
                content_type=file.content_type, size=file.size,
                charset=file.charset)
            file.seek(0)
            buf = file.read()
            tmp.write(buf)
            print "Wrote %d bytes" % len(buf)
            tmp.flush()
        else:
            tmp = file
            
        if isinstance(tmp, TemporaryUploadedFile):
            path = tmp.temporary_file_path()
        else:
            path = tmp.name
        
        return (tmp, path)

    def extract_text_using_tool(self, file, tool, format_name, original_name):
        (tmp, path) = self.ensure_saved(file)

        try:         
            try:
                process = self.safe_popen(tool, path)
            except Exception as e:
                raise Exception('Failed to convert %s document: %s' % 
                    (format_name, e));
                
            (out, err) = process.communicate()
            if err != '' and err != "Using ODF/OOXML parser.\n" \
                and err != "Using XLS parser.\n":
                # os.system("ls -la /tmp")
                # err = err.replace(path, original_name)
                raise Exception('Failed to convert %s document: %s' % 
                    (format_name, err));
        finally:
            tmp.close()

        return out

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

        if document.file is None:
            return

        # http://redmine.djity.net/projects/pythontika/wiki
        import tika
        tika.getVMEnv().attachCurrentThread()
        parser = tika.AutoDetectParser()

        real_file_object = document.file.file

        if isinstance(real_file_object, InMemoryUploadedFile):
            buffer = document.file.read()
            input = tika.StringBufferInputStream(buffer)
        else:
            if isinstance(real_file_object, TemporaryUploadedFile):
                path = real_file_object.temporary_file_path()
            else:
                path = real_file_object.name
            input = tika.FileInputStream(tika.File(path))
        
        # Create handler for content, metadata and context
        content = tika.BodyContentHandler()
        metadata = tika.Metadata()
        context = tika.ParseContext()

        # Parse the data and display result
        parser.parse(input, content, metadata, context)
        return content.toString()
