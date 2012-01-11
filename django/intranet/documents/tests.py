"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.admin.models import User
from documents.models import Document
from documents.admin import DocumentAdmin
from django.contrib import admin 

class DocumentsModuleTest(TestCase):
    def setUp(self):
        self.john = User.objects.create_user('john', 'lennon@thebeatles.com',
            'johnpassword')
        
    def test_create_document_object(self):
        doc = Document(title="foo", description="bar", file="whee",
            author_id=self.john.id)
        doc.save()
        self.assertItemsEqual([doc], Document.objects.all())

    def test_document_admin_class(self):
        self.assertIn(Document, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Document], DocumentAdmin)
        