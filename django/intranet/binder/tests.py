"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

import settings
import documents.urls
import binder.templatetags.menu as menu_tag

class BinderTest(TestCase):
    def test_front_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        g = response.context['global']
        self.assertEqual("/", g['path'])
        self.assertEqual(settings.APP_TITLE, g['app_title'])
        
        main_menu = g['main_menu']
        self.assertEqual("Home", main_menu[0].title)
        self.assertEqual("front_page", main_menu[0].url_name)
        self.assertEqual("Documents", main_menu[1].title)
        self.assertEqual(documents.urls.urlpatterns[0].name,
            main_menu[1].url_name)
        
    def test_menu_tag(self):
        response = self.client.get('/')
        self.assertEqual('<li class="selected"><a href="/">Home</a></li>',
            menu_tag.menu_item(response.context, 'front_page', 'Home'))
            