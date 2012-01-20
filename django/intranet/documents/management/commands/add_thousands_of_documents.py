import os, os.path
import random
from django.core.management.base import NoArgsCommand, CommandError
from django.core.files.base import File
from documents.models import Document, DocumentType
from binder.models import Program, IntranetUser

class Command(NoArgsCommand):
    help = 'Add thousands of documents to the Whoosh search index to stress it'

    def handle_noargs(self, **options):
        doc_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
            '..', '..', 'doc')
        
        doctypes = DocumentType.objects.all()
        programs = Program.objects.all()
        users = IntranetUser.objects.all()
        
        for i in range(1000):
            for f in os.listdir(doc_dir):
                doc = Document()
                doc.title = random.random()
                doc.file = File(open(os.path.join(doc_dir, f)))
                doc.notes = random.random()
                doc.document_type = random.choice(doctypes)
                doc.save()
                doc.programs = random.sample(programs, 2)
                doc.authors = random.sample(users, 1)
