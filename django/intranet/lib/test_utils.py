from django.test import TestCase

class AptivateEnhancedTestCase(TestCase):
    def setUp(self):
        TestCase.setUp(self)

        from django.conf import settings
        from haystack.constants import DEFAULT_ALIAS
        settings.HAYSTACK_CONNECTIONS[DEFAULT_ALIAS]['PATH'] = '/dev/shm/whoosh'

        from haystack import connections
        self.search_conn = connections[DEFAULT_ALIAS]
        self.search_conn.get_backend().delete_index()

        self.unified_index = self.search_conn.get_unified_index()
        
    def assign_fixture_to_filefield(self, fixture_file_name, filefield):

        import sys
        module = sys.modules[self.__class__.__module__]

        import os.path
        path = os.path.join(os.path.dirname(module.__file__), 'fixtures',
            fixture_file_name)
        
        from django.core.files import File as DjangoFile
        df = DjangoFile(open(path))
        filefield.save(fixture_file_name, df, save=False) 
