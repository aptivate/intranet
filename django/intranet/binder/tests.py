"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

class BinderTest(TestCase):
    def test_front_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)        
