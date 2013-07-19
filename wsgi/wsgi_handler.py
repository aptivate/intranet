import os, sys, site

# find the project name from project_settings
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(os.path.join(project_dir, 'deploy'))
from project_settings import project_name

# ensure the virtualenv for this instance is added
ve_dir = os.path.join(project_dir, 'django', project_name, '.ve')
paths_to_search = (
    ('lib', 'python2.7', 'site-packages'),
    ('lib', 'python2.6', 'site-packages'),
    ('lib', 'site-packages')
    )

found_ve_path = None
searched_ve_paths = []
for path in paths_to_search:
    expanded_path = os.path.join(ve_dir, *path)
    searched_ve_paths.append(expanded_path)

    if os.path.exists(expanded_path):
        site.addsitedir(expanded_path)
        found_ve_path = expanded_path

if not found_ve_path:
    raise Exception("Did not find a virtualenv in any of these directories: " +
        "%s" % searched_ve_paths)

# not sure about this - might be required for packages installed from
# git/svn etc
#site.addsitedir(os.path.join(project_dir, 'django', project_name, '.ve', 'src'))
sys.path.append(os.path.join(project_dir, 'django'))
sys.path.append(os.path.join(project_dir, 'django', project_name))

# this basically does:
# os.environ['PROJECT_NAME_HOME'] = '/var/django/project_name/dev/'
os.environ[project_name.upper() + '_HOME'] = project_dir

# this does the same setup as "./manage.py runserver", ensuring we get the
# same behaviour on apache as when developing.
# See http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html
# for the rationale.

from django.conf import settings

import django.core.management
django.core.management.setup_environ(settings)
utility = django.core.management.ManagementUtility()
command = utility.fetch_command('runserver')
command.validate()

import django.conf
import django.utils
django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)

try:
    active_monkeys = settings.MONKEY_PATCHES
except AttributeError:
    active_monkeys = []

from django.utils import importlib
for module_name in active_monkeys:
    importlib.import_module(module_name)

# Now we do the normal django set up
import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

# Dozer is something that can help debug memory leaks
#from dozer import Dozer
#application = Dozer(application)
