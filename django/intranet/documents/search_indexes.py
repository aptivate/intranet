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

        document.file.open()
        
        try:
            f = document.file.file
            buffer = f.read()
            magic = Magic(mime=False).from_buffer(buffer)
            mime = Magic(mime=True).from_buffer(buffer)
            mime = mime.replace('; charset=binary', '')
            f.seek(0) # reset to beginning
            
            # we can't trust file(1) to identify 
            if mime == 'application/zip' or mime == 'application/x-zip' \
                or magic == 'Microsoft Word 2007+' \
                or magic == 'Microsoft Excel 2007+' \
                or magic == 'Microsoft PowerPoint 2007+':
                # is it an Open Office XML file?
                zip = ZipFile(document.file, 'r')
                names = zip.namelist()
                
                if 'word/document.xml' in names:
                    # looks like a Word (DOCX) file
                    document = docx.opendocx(document.file)
                    paratextlist = docx.getdocumenttext(document)
                    return "\n\n".join(paratextlist)
                
                if 'ppt/presentation.xml' in names or \
                    'xl/workbook.xml' in names:
                    # looks like a PowerPoint (PPTX) or Excel (XLSX) file
                    from settings import DOCTOTEXT_PATH
                    return self.extract_text_using_tool(f, 
                        ['sh', DOCTOTEXT_PATH], 'PowerPoint XML',
                        document.file.name)
                
                raise Exception("Don't know how to index a ZIP file")
            
            elif mime == 'application/vnd.ms-excel':
                from settings import DOCTOTEXT_PATH
                return self.extract_text_using_tool(f, 
                    ['sh', DOCTOTEXT_PATH], 'Excel', document.file.name)
                
            elif mime == 'application/msword':
                return self.extract_text_using_tool(f, ['antiword'], 'Word',
                    document.file.name)

            elif mime == 'application/pdf':
                rsrcmgr = PDFResourceManager(caching=True)
                outfp = StringIO()
                device = TextConverterWithoutPageBreaks(rsrcmgr, outfp,
                    codec='utf-8', laparams=LAParams())
                process_pdf(rsrcmgr, device, f, caching=True,
                    check_extractable=False)
                return outfp.getvalue()
            
            elif mime.startswith('text/'):
                data = f.read(1<<26) # 64 MB
                return data
                
            else:
                raise Exception("Don't know how to index %s documents" %
                    mime)
                # data = f.read(1<<26) # 64 MB
                # return data
        finally:
            if f is not None:
                f.close()
