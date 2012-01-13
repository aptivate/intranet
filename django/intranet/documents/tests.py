"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from StringIO import StringIO
from lxml import etree

from django.test import TestCase
from django.contrib import admin 
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth import login
from django.conf import settings as django_settings
from django.core.urlresolvers import reverse
from django.test.client import Client, RequestFactory, encode_multipart, \
    MULTIPART_CONTENT, BOUNDARY

from django.utils.functional import curry

from documents.admin import DocumentAdmin
from documents.models import Document, Program, DocumentType

class SuperClient(Client):
    def get(self, *args):
        response = Client.get(self, *args)
        return self.capture_results('get', response, *args)

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
        return self.capture_results('post', response, path, data,
            content_type, **extra)
    
    def capture_results(self, method_name, response, *args):
        # print("%s.%s(%s)" % (self, method_name, args))
        self.last_method = method_name
        self.last_method_args = args
        # http://stackoverflow.com/questions/5170252/whats-the-best-way-to-handle-nbsp-like-entities-in-xml-documents-with-lxml
        x = """<?xml version="1.0" encoding="utf-8"?>\n""" + response.content
        p = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
        r = etree.fromstring(x, p)
        setattr(response, 'parsed', r)
        return response
        
    def retry(self):
        """Try the same request again (e.g. after login)."""
        return getattr(self, self.last_method)(*self.last_method_args)
    
    def request(self, **request):
        # print "request = %s" % request
        return Client.request(self, **request)

class DocumentsModuleTest(TestCase):
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
        from django.contrib.contenttypes.models import ContentType
        document_ct = ContentType.objects.get(app_label='documents',
            model='document')

        add_doc = Permission.objects.get(content_type=document_ct,
            codename="add_document")
        user = Group.objects.get(name='User')
        self.assertIn(add_doc, user.permissions.all(),
            'add document permission for User is required for tests to run')
        
        self.john = User.objects.create_user('john', 'lennon@thebeatles.com',
            'johnpassword')
        self.john.is_staff = True
        self.john.groups.add(user)
        self.john.save()

        # run a POST just to get a response with its embedded request...
        self.login()
        response = self.client.post(reverse('admin:documents_document_add'))
        # fails with PermissionDenied if our permissions are wrong
         
        # response.request.__dict__ = {}
        # setattr(response.request, 'user', self.john)
        # that we can pass to has_add_permission()
        # docadmin = admin.site._registry[Document]
        # self.assertTrue(docadmin.has_add_permission(response.request),
        #    "Adding permission to test user didn't work as expected")
        
        """
        self.wrap(self.client, 'get')
        self.wrap(self.client, 'post')
        """
        self.client = SuperClient()

    """        
    def retry(self):
        "Try the same request again (e.g. after login)."
        return getattr(self.client, self.last_method)(*self.last_method_args)
    """
    
    def login(self):
        self.assertTrue(self.client.login(username=self.john.username,
            password='johnpassword'), "Login failed")
        self.assertIn(django_settings.SESSION_COOKIE_NAME, self.client.cookies) 
        print "session cookie = %s" % (
            self.client.cookies[django_settings.SESSION_COOKIE_NAME])
        
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
            })
        self.assertEqual("Please check your user name and password and try again.",
            self.extract_error_message(response),
            "POST without login did not fail as expected: %s" % response.content)

        self.login()
        response = self.client.retry()
        # print response.content
        # print "%s" % response.context
        self.assertDictEqual({}, response.context['adminform'].form.errors)
        for fieldset in response.context['adminform']:
            for line in fieldset:
                self.assertIsNone(line.errors)
                for field in line:
                    self.assertIsNone(field.errors)
        self.assertIsNone(response.context['adminform'].form.non_field_errors)
        self.assertIsNone(self.extract_error_message(response))

        # did it save?
        doc = Document.objects.get()
        self.assertEqual('foo', doc.title)
        self.assertEqual('bar', doc.description)
        self.assertSequenceEqual([self.john.id], doc.authors.all())
        self.assertEqual('boink.png', doc.file)
    
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