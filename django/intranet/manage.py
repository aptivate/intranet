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

def replacement_get_response(self, request):
    """
    Returns an HttpResponse object for the given HttpRequest. Unlike
    the original get_response, this does not catch exceptions.
    """
    
    from django.core import exceptions, urlresolvers
    from django.conf import settings

    # Setup default url resolver for this thread, this code is outside
    # the try/except so we don't get a spurious "unbound local
    # variable" exception in the event an exception is raised before
    # resolver is set
    urlconf = settings.ROOT_URLCONF
    urlresolvers.set_urlconf(urlconf)
    resolver = urlresolvers.RegexURLResolver(r'^/', urlconf)
    response = None
    # Apply request middleware
    for middleware_method in self._request_middleware:
        response = middleware_method(request)
        if response:
            break

    if response is None:
        if hasattr(request, "urlconf"):
            # Reset url resolver with a custom urlconf.
            urlconf = request.urlconf
            urlresolvers.set_urlconf(urlconf)
            resolver = urlresolvers.RegexURLResolver(r'^/', urlconf)

        callback, callback_args, callback_kwargs = resolver.resolve(
                request.path_info)

        # Apply view middleware
        for middleware_method in self._view_middleware:
            response = middleware_method(request, callback, callback_args, callback_kwargs)
            if response:
                break

    if response is None:
        try:
            response = callback(request, *callback_args, **callback_kwargs)
        except Exception, e:
            # If the view raised an exception, run it through exception
            # middleware, and if the exception middleware returns a
            # response, use that. Otherwise, reraise the exception.
            for middleware_method in self._exception_middleware:
                response = middleware_method(request, e)
                if response:
                    break
            if response is None:
                raise

    # Complain if the view returned None (a common error).
    if response is None:
        try:
            view_name = callback.func_name # If it's a function
        except AttributeError:
            view_name = callback.__class__.__name__ + '.__call__' # If it's a class
        raise ValueError("The view %s.%s didn't return an HttpResponse object." % (callback.__module__, view_name))

    # If the response supports deferred rendering, apply template
    # response middleware and the render the response
    if hasattr(response, 'render') and callable(response.render):
        for middleware_method in self._template_response_middleware:
            response = middleware_method(request, response)
        response.render()

    # Reset URLconf for this thread on the way out for complete
    # isolation of request.urlconf
    urlresolvers.set_urlconf(None)

    # Apply response middleware, regardless of the response
    for middleware_method in self._response_middleware:
        response = middleware_method(request, response)
    response = self.apply_response_fixes(request, response)

    return response

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.test.utils

original_test_setup = django.test.utils.setup_test_environment

def replacement_test_setup():
    original_test_setup()
    
    from django.core.handlers.base import BaseHandler
    original_get_response = BaseHandler.get_response
    BaseHandler.get_response = replacement_get_response 
    
django.test.utils.setup_test_environment = replacement_test_setup

# run django
from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError as e:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n%s\n" % (__file__, e))
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
