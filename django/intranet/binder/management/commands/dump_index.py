from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):
    help = 'Dump the contents of the Whoosh search index'

    def handle_noargs(self, **options):
        from whoosh.index import open_dir
        from settings import HAYSTACK_WHOOSH_PATH
        ix = open_dir(HAYSTACK_WHOOSH_PATH)
        
        with ix.searcher() as searcher:
            from whoosh import query
            q = query.Every()
            results = searcher.search(q)
            for i, r in enumerate(results):
                self.stdout.write('result %d = %s\n' % (i, r))
