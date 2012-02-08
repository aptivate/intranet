import os, sys, site

# find the project name from project_settings
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(os.path.join(project_dir, 'deploy'))
from project_settings import project_name

# ensure the virtualenv for this instance is added
site.addsitedir(os.path.join(project_dir, 'django', project_name, '.ve', 
                              'lib', 'python2.6', 'site-packages'))

# not sure about this - might be required for packages installed from
# git/svn etc
#site.addsitedir(os.path.join(project_dir, 'django', project_name, '.ve', 'src'))
sys.path.append(os.path.join(project_dir, 'django'))
sys.path.append(os.path.join(project_dir, 'django', project_name))


#print >> sys.stderr, sys.path

os.environ['DJANGO_SETTINGS_MODULE'] = project_name + '.settings'

# this basically does:
# os.environ['PROJECT_NAME_HOME'] = '/var/django/project_name/dev/'
os.environ[project_name.upper() + '_HOME'] = os.path.join('/var/django', project_name, 'dev')

import binder.monkeypatch

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

