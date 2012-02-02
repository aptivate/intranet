"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from StringIO import StringIO
from lxml import etree

from django.test import TestCase
from django.contrib import admin 
from binder.models import IntranetUser
from django.contrib.auth import login
from django.conf import settings as django_settings
from django.core.urlresolvers import reverse
from django.test.client import Client, RequestFactory, encode_multipart, \
    MULTIPART_CONTENT, BOUNDARY

from django.utils.functional import curry

from documents.admin import DocumentAdmin
from documents.models import Document, DocumentType
from binder.models import Program

class SuperClient(Client):
    def get(self, *args, **extra):
        response = Client.get(self, *args)
        return self.capture_results('get', response, *args, **extra)

    def post(self, path, data={}, content_type=MULTIPART_CONTENT,
             **extra):
        """
        Pickle the request first, in case it contains a StringIO (file upload)
        that can't be read twice.
        
        If the data doesn't have an items() method, then it's probably already
        been converted to a string (encoded), and if we try again we'll call
        the nonexistent items() method and fail, so just don't encode it at
        all."""
        if content_type == MULTIPART_CONTENT and \
            getattr(data, 'items', None) is not None:
            data = encode_multipart(BOUNDARY, data)
        
        # print "session cookie = %s" % (
        # self.cookies[django_settings.SESSION_COOKIE_NAME])
        response = Client.post(self, path, data, content_type, **extra)
        
        if response is None:
            raise Exception("POST method responded with None!")
        
        return self.capture_results('post', response, path, data,
            content_type, **extra)
    
    def capture_results(self, method_name, response, *args, **kwargs):
        # print("%s.%s(%s)" % (self, method_name, args))
        self.last_method = method_name
        self.last_method_args = args
        self.last_method_kwargs = kwargs
        
        if not response.content:
            return response # without setting the parsed attribute
        
        # http://stackoverflow.com/questions/5170252/whats-the-best-way-to-handle-nbsp-like-entities-in-xml-documents-with-lxml
        x = """<?xml version="1.0" encoding="utf-8"?>\n""" + response.content
        p = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
        
        try:
            r = etree.fromstring(x, p)
        except SyntaxError as e:
            import re
            match = re.match('Opening and ending tag mismatch: ' +
                '(\w+) line (\d+) and (\w+), line (\d+), column (\d+)', str(e))
            if match:
                lineno = int(match.group(2))
            else:
                match = re.match('.*, line (\d+), column (\d+)', str(e))
                if match:
                    lineno = int(match.group(1))

            if not match:            
                lineno = e.lineno
                
            lines = x.splitlines(True)
            if lineno is not None:
                first_line = max(lineno - 5, 1)
                last_line = min(lineno + 5, len(lines))
                print x
                print "Context (line %s):\n%s" % (lineno,
                    "".join(lines[first_line:last_line]))
            else:
                print repr(e)
            raise e  
        
        setattr(response, 'parsed', r)
        return response
        
    def retry(self):
        """Try the same request again (e.g. after login)."""
        # print "retry kwargs = %s" % self.last_method_kwargs 
        return getattr(self, self.last_method)(*self.last_method_args,
            **self.last_method_kwargs)
    
    def request(self, **request):
        # print "request = %s" % request
        return Client.request(self, **request)

class DocumentsModuleTest(TestCase):
    fixtures = ['test_permissions', 'test_users']
    
    """
    def wrap(self, instance, method_name):
        old_method = getattr(instance, method_name)
        
        def new_method(*args):
            print("%s.%s(%s)" % (instance, method_name, args))
            self.last_method = method_name
            self.last_method_args = args
            response = old_method(*args)
            x = '<?xml version="1.0" encoding="utf-8"?>' + "\n" + response.content
            p = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
            r = etree.fromstring(x, p)
            setattr(response, 'parsed', r)
            return response
        
        setattr(instance, method_name, new_method)
    """
     
    def setUp(self):
        self.john = IntranetUser.objects.get(username='john')

        # run a POST just to get a response with its embedded request...
        self.login()
        response = self.client.post(reverse('admin:documents_document_add'))
        # fails with PermissionDenied if our permissions are wrong
        self.client = SuperClient()
    
    def login(self):
        self.assertTrue(self.client.login(username=self.john.username,
            password='johnpassword'), "Login failed")
        self.assertIn(django_settings.SESSION_COOKIE_NAME, self.client.cookies) 
        """
        print "session cookie = %s" % (
            self.client.cookies[django_settings.SESSION_COOKIE_NAME])
        """
        
    def test_create_document_object(self):
        doc = Document(title="foo", document_type=DocumentType.objects.all()[0],
            file="whee", notes="bonk")
        doc.save()
        doc.programs = Program.objects.all()[:2]  
        doc.authors = [self.john.id]
        self.assertItemsEqual([doc], Document.objects.all())

    def test_document_admin_class(self):
        self.assertIn(Document, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Document], DocumentAdmin)
        
    def extract_error_message(self, response):
        error_message = response.parsed.findtext('.//div[@class="error-message"]')
        if error_message is None:
            error_message = response.parsed.findtext('.//p[@class="errornote"]')
        
        if error_message is not None:
            # extract individual field errors, if any
            more_error_messages = response.parsed.findtext('.//td[@class="errors-cell"]')
            if more_error_messages is not None:
                error_message += more_error_messages
            
            # trim and canonicalise whitespace
            error_message = error_message.strip()
            import re
            error_message = re.sub('\\s+', ' ', error_message)
            
        # return message or None
        return error_message

    def extract_error_message_fallback(self, response):
        error_message = self.extract_error_message(response)
        if error_message is None:
            error_message = response.content
        return error_message
        
    def test_create_document_admin(self):
        response = self.client.get(reverse('admin:documents_document_add'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(None, self.extract_error_message(response))
        # self.assertEqual('admin/login.html', response.template_name)
        
        f = StringIO('foobar')
        setattr(f, 'name', 'boink.png')

        # without login, should fail and tell us to log in        
        response = self.client.post(reverse('admin:documents_document_add'),
            {
                'title': 'foo',
                'document_type': DocumentType.objects.all()[0].id,
                'programs': Program.objects.all()[0].id,
                'file': f,
                'notes': 'whee',
                'authors': self.john.id,
            }, follow=True)
        self.assertEqual("Please check your user name and password and try again.",
            self.extract_error_message(response),
            "POST without login did not fail as expected: %s" % response.content)

        self.login()
        response = self.client.retry()
        # print response.content
        # print "%s" % response.context
        self.assertTrue(hasattr(response, 'context'), "Missing context " +
            "in response: %s: %s" % (response, dir(response)))
        self.assertIsNotNone(response.context, "Empty context in response: " +
            "%s: %s" % (response, dir(response)))
        
        # If this succeeds, we get redirected to the changelist_view.
        # If it fails, we get sent back to the edit page, with an error.
        if 'adminform' in response.context: 
            self.assertDictEqual({}, response.context['adminform'].form.errors)
            for fieldset in response.context['adminform']:
                for line in fieldset:
                    self.assertIsNone(line.errors)
                    for field in line:
                        self.assertIsNone(field.errors)
            self.assertIsNone(response.context['adminform'].form.non_field_errors)
            self.assertIsNone(self.extract_error_message(response))

        self.assertNotIn('adminform', response.context, "Unexpected " +
            "admin form in response context: %s" % response)
        self.assertIn('cl', response.context, "Missing changelist " +
            "in response context: %s" % response)

        # did it save?
        doc = Document.objects.get()
        self.assertEqual('foo', doc.title)
        self.assertEqual(DocumentType.objects.all()[0], doc.document_type)
        self.assertItemsEqual([Program.objects.all()[0]], doc.programs.all())
        import re
        self.assertRegexpMatches(doc.file.name, 'boink(_\d+)?.png',
            "Wrong name on uploaded file")
        self.assertEqual('whee', doc.notes)
        self.assertItemsEqual([self.john], doc.authors.all())
    
    """
    def test_admin_submit_with_error_doesnt_lose_file_data(self):
        from django.db import models
        class TestDocument(models.Model):
            name = models.CharField(max_length=255, unique=True)
            file = models.FileField(upload_to='documents')
        from django.core.management import ManagementUtility
        ManagementUtility(['dummy', 'syncdb']).execute()
        admin.site.register(TestDocument, admin.ModelAdmin)
        """
    
        # self.client.