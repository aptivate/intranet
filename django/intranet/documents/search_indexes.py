import datetime
import docx
import subprocess

from django.db.models import signals
from django.core.files.uploadedfile import TemporaryUploadedFile, \
    InMemoryUploadedFile
from haystack.indexes import *
from haystack import site
from magic import Magic
from StringIO import StringIO

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
        """
        signals.pre_save.connect(self.test_object, sender=model,
            dispatch_uid="document_index_on_validate_document")
        """
        Document.on_validate.connect(self.test_object, sender=model,
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

    def safe_popen(self, command, *args):
        cmd_with_args = [command]
        cmd_with_args.extend(args)
        
        try:
            return subprocess.Popen(cmd_with_args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        except (OSError, IOError) as e:
            raise Exception('%s: %s' % (command, e))

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
        
        try:
            document.file.open()
            f = document.file.file
            magic = Magic(mime=True)
            mime = magic.from_buffer(f.read())
            f.seek(0) # reset to beginning
        
            if mime == 'application/zip' or mime == 'application/x-zip':
                # is it a DOCX file?
                document = docx.opendocx(document.file)
                paratextlist = docx.getdocumenttext(document)
                return "\n\n".join(paratextlist)
            elif mime == 'application/msword':
                if isinstance(f, InMemoryUploadedFile):
                    tmp = TemporaryUploadedFile(name=f.name,
                        content_type=f.content_type, size=f.size,
                        charset=f.charset)
                    tmp.write(f.read())
                    f.close()
                    f = tmp
                    
                if isinstance(f, TemporaryUploadedFile):
                    path = f.temporary_file_path()
                else:
                    path = f.name
                
                try:
                    process = self.safe_popen('antiword', path)
                except Exception as e:
                    raise Exception('Failed to convert Word document: %s' %
                        e);
                    
                (out, err) = process.communicate()
                if err != '':
                    err = err.replace(path, document.file.name)
                    raise Exception('Failed to convert Word document: %s' %
                        err);
                return out
            elif mime == 'application/pdf':
                rsrcmgr = PDFResourceManager(caching=True)
                outfp = StringIO()
                device = TextConverterWithoutPageBreaks(rsrcmgr, outfp,
                    codec='utf-8', laparams=LAParams())
                process_pdf(rsrcmgr, device, f, caching=True,
                    check_extractable=False)
                return outfp.getvalue()
            else:
                raise Exception("Don't know how to index %s documents" %
                    mime)
                # data = f.read(1<<26) # 64 MB
                # return data
        finally:
            if f is not None:
                f.close()

site.register(Document, DocumentIndex)