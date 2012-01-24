#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
from os import path
import shutil, sys, virtualenv, subprocess

PROJECT_ROOT = path.abspath(path.dirname(__file__))
REQUIREMENTS = path.abspath(path.join(PROJECT_ROOT, '..', '..', 'deploy', 'pip_packages.txt'))

VE_ROOT = path.join(PROJECT_ROOT, '.ve')
VE_TIMESTAMP = path.join(VE_ROOT, 'timestamp')

envtime = path.exists(VE_ROOT) and path.getmtime(VE_ROOT) or 0
envreqs = path.exists(VE_TIMESTAMP) and path.getmtime(VE_TIMESTAMP) or 0
envspec = path.getmtime(REQUIREMENTS)

def go_to_ve():
    # going into ve
    if not sys.prefix == VE_ROOT:
        if sys.platform == 'win32':
            python = path.join(VE_ROOT, 'Scripts', 'python.exe')
        else:
            python = path.join(VE_ROOT, 'bin', 'python')
            
        retcode = subprocess.call([python, __file__] + sys.argv[1:])
        sys.exit(retcode)

update_ve = 'update_ve' in sys.argv
if update_ve or envtime < envspec or envreqs < envspec:
    if update_ve:
        # install ve
        if envtime < envspec:
            if path.exists(VE_ROOT):
                shutil.rmtree(VE_ROOT)
            virtualenv.logger = virtualenv.Logger(consumers=[])
            virtualenv.create_environment(VE_ROOT, site_packages=True)
            #virtualenv.create_environment(VE_ROOT, site_packages=False)

        go_to_ve()    

        # check requirements
        if update_ve or envreqs < envspec:
            import pip
            pip.main(initial_args=['install', '-r', REQUIREMENTS])
            file(VE_TIMESTAMP, 'w').close()
        sys.exit(0)
    else:
        print "VirtualEnv need to be updated"
        print "Run ./manage.py update_ve"
        sys.exit(1)

go_to_ve()

# run django
from django.core.management import setup_environ, ManagementUtility

try:
    import settings # Assumed to be in the same directory.
except ImportError as e:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n%s\n" % (__file__, e))
    sys.exit(1)

def execute_manager(settings_mod, argv=None):
    """
    Like execute_from_command_line(), but for use by manage.py, a
    project-specific django-admin.py utility.
    """
    setup_environ(settings_mod)
    import lib.monkeypatch
    utility = ManagementUtility(argv)
    utility.execute()

if __name__ == "__main__":
    execute_manager(settings)
