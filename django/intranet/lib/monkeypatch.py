# https://bitbucket.org/ikasamt/googleappenginejukebox/src/438c44768ab5/plugins/alias_method_chain/__init__.py

import logging

def alias_method_chain(clazz, old_name, name):
  setattr(clazz, "%s_without_%s" % (old_name, name), clazz)
  setattr(clazz, old_name, getattr(clazz, "%s_with_%s" % (old_name, name)))

"""
class A: 
  def dan(self): 
    print "dan"

class B(A):
  def dan_with_kogai(self):
    self.dan_without_kogai()
    print "kogai"

alias_method_chain(B, A.dan, "kogai")
B().dan()
"""

from django.utils.functional import curry

def patch(class_or_instance, method_name, replacement_function):
    original_function = getattr(class_or_instance, method_name)
    setattr(class_or_instance, method_name, 
        curry(replacement_function, original_function))

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.test.client import ClientHandler
def get_response_with_exception_passthru(original_function, self, request):
    """
    Returns an HttpResponse object for the given HttpRequest. Unlike
    the original get_response, this does not catch exceptions.
    """
    
    # print("get_response(%s)" % request)
    
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
patch(ClientHandler, 'get_response', get_response_with_exception_passthru) 

from django.db.models.query import QuerySet
def queryset_get_with_exception_detail(original_function, self, *args, **kwargs):
    """
    Performs the query and returns a single object matching the given
    keyword arguments.
    """
    clone = self.filter(*args, **kwargs)
    if self.query.can_filter():
        clone = clone.order_by()
    num = len(clone)
    if num == 1:
        return clone._result_cache[0]
    if not num:
        raise self.model.DoesNotExist(("%s matching query does not exist " +
            "(query was: %s, %s)") % (self.model._meta.object_name,
                args, kwargs))
    raise self.model.MultipleObjectsReturned("get() returned more than one %s -- it returned %s! Lookup parameters were %s"
            % (self.model._meta.object_name, num, kwargs))
patch(QuerySet, 'get', queryset_get_with_exception_detail)

from django.forms.fields import FileField
def to_python_with_debugging(original_function, self, data):
    print "data = %s" % data
    return original_function(self, data)
patch(FileField, 'to_python', to_python_with_debugging)

from django.contrib.admin.sites import AdminSite
def has_permission_with_debugging(original_function, self, request):
    """
    Returns True if the given HttpRequest has permission to view
    *at least one* page in the admin site.
    """
    has_permission = original_function(self, request)
    # print "has_permission = %s" % has_permission
    # print "request.user = %s" % request.user
    # print "request.user.is_active = %s" % request.user.is_active
    # print "request.user.is_staff = %s" % request.user.is_staff
    return has_permission
patch(AdminSite, 'has_permission', has_permission_with_debugging)

import django.contrib.auth.views
def login_with_debugging(original_function, request,
    template_name='registration/login.html',
    redirect_field_name=django.contrib.auth.views.REDIRECT_FIELD_NAME,
    authentication_form=django.contrib.auth.views.AuthenticationForm,
    current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        print "form.is_valid = %s" % form.is_valid()
        
        username = form['username'].value()
        password = form['password'].value()
        print "username = %s" % username
        print "password = %s" % password

        if username and password:
            from django.contrib.auth import authenticate
            form.user_cache = authenticate(username=username, password=password)
            print "user_cache = %s" % form.user_cache
            print "get_user = %s" % form.get_user()
    
    print "user_cache.is_active = %s" % form.user_cache.is_active
    print "user_cache.is_staff = %s" % form.user_cache.is_staff
    
    result = original_function(request, template_name, redirect_field_name,
        authentication_form, current_app, extra_context)
    print "result = %s" % result
    return result
# patch(django.contrib.auth.views, 'login', login_with_debugging)

from django.test.client import RequestFactory, MULTIPART_CONTENT, urlparse, \
    FakePayload
def post_with_string_data_support(original_function, self, path, data={},
    content_type=MULTIPART_CONTENT, **extra):
    """If the data doesn't have an items() method, then it's probably already
    been converted to a string (encoded), and if we try again we'll call
    the nonexistent items() method and fail, so just don't encode it at
    all."""
    if content_type == MULTIPART_CONTENT and getattr(data, 'items', None) is None:
        parsed = urlparse(path)
        r = {
            'CONTENT_LENGTH': len(data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   parsed[4],
            'REQUEST_METHOD': 'POST',
            'wsgi.input':     FakePayload(data),
        }
        r.update(extra)
        return self.request(**r)
    else:
        return original_function(self, path, data, content_type, **extra)
patch(RequestFactory, 'post', post_with_string_data_support)

from django.forms.models import ModelFormMetaclass
def new_with_debugging(original_function, cls, name, bases, attrs):
    from django.forms.forms import get_declared_fields
    print 'cls = %s' % cls
    print 'bases = %s' % bases
    print 'attrs = %s' % attrs
    print "declared_fields = %s" % get_declared_fields(bases, attrs, False)
    return original_function(cls, name, bases, attrs)
# patch(ModelFormMetaclass, '__new__', new_with_debugging)

import django.contrib.admin.validation
def check_formfield_with_debugging(original_function, cls, model, opts, label, field):
    print 'checking %s.%s: base_fields = %s\n' % (cls.__name__, field,
        getattr(cls.form, 'base_fields'))
    return original_function(cls, model, opts, label, field)

"""
patch(django.contrib.admin.validation, 'check_formfield', 
    check_formfield_with_debugging)
"""