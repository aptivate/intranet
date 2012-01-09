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

# this basically does:
# os.environ['PROJECT_NAME_HOME'] = '/var/django/project_name/dev/'
os.environ[project_name.upper() + '_HOME'] = os.path.join('/var/django', project_name, 'dev')

# this does the same setup as "./manage.py runserver", ensuring we get the
# same behaviour on apache as when developing.
# See http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html
# for the rationale.

# import project_name.settings as settings
# we want the above, but to use a string we do
import imp
fp, pathname, desc = imp.find_module(os.path.join(project_dir, 'django',
                                   project_name, 'settings')
try:
    settings = imp.load_module(project_name+'.settings', fp, pathname, desc)
finally:
    if fp:
        fp.close()

import django.core.management
django.core.management.setup_environ(settings)
utility = django.core.management.ManagementUtility()
command = utility.fetch_command('runserver')
command.validate()

import django.conf
import django.utils
django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)

# Now we do the normal django set up
import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

# Dozer is something that can help debug memory leaks
#from dozer import Dozer
#application = Dozer(application)
