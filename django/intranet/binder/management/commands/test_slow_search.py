from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):
    help = 'Dump the contents of the Whoosh search index'

    def handle_noargs(self, **options):
        from whoosh.index import open_dir
        from whoosh.qparser import QueryParser
        
        from settings import HAYSTACK_CONNECTIONS
        ix = open_dir(HAYSTACK_CONNECTIONS['default']['PATH'])
        
        with ix.searcher() as searcher:
            parser = QueryParser("text", ix.schema)

            q = parser.parse(u'(programs:4 or programs:5)')
            print "or => %s" % q
            results = searcher.search(q)
            print len(results)
            
            q = parser.parse(u'(programs:4 OR programs:5)')
            print "OR => %s" % q
            results = searcher.search(q, optimize=False)
            print len(results)
