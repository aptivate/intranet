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
    # print "data = %s" % data
    return original_function(self, data)
# patch(FileField, 'to_python', to_python_with_debugging)

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
# patch(AdminSite, 'has_permission', has_permission_with_debugging)

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
            print "user_cache = %s" % repr(form.user_cache)
            print "get_user = %s" % form.get_user()
    
    # print "user_cache.is_active = %s" % form.user_cache.is_active
    # print "user_cache.is_staff = %s" % form.user_cache.is_staff
    
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
# patch(django.contrib.admin.validation, 'check_formfield', 
#     check_formfield_with_debugging)

from django.forms.models import BaseModelForm, InlineForeignKeyField, \
    construct_instance, NON_FIELD_ERRORS
    
def is_valid_with_debugging(original_function, self):
    print "is_valid: errors before = %s" % self._errors
    print "is_bound = %s" % self.is_bound
    print "self.empty_permitted = %s" % self.empty_permitted 
    print "self.has_changed = %s" % self.has_changed()
    ret = original_function(self)
    print "is_valid = %s" % ret
    print "is_valid: errors after = %s" % self._errors
    return ret
# patch(BaseModelForm, 'is_valid', is_valid_with_debugging)

def post_clean(original_function, self):
    print "post_clean: instance = %s" % self.instance
    return original_function(self)
# patch(BaseModelForm, '_post_clean', post_clean)

def update_errors(original_function, self, message_dict):
    print "update_errors: %s" % message_dict
    return original_function(self, message_dict)
# patch(BaseModelForm, '_update_errors', update_errors)

from django.db.models.base import Model
from django.core.exceptions import ValidationError
def full_clean_with_debugging(original_function, self, exclude=None):
    errors = {}

    print "full_clean starting"

    # Form.clean() is run even if other validation fails, so do the
    # same with Model.clean() for consistency.
    try:
        self.clean()
    except ValidationError, e:
        errors = e.update_error_dict(errors)
    except:
        print "Model.clean() raised an unknown exception"
        raise
        
    print "errors after Model.clean() = %s" % errors

    try:
        return original_function(self, exclude)
    except Exception as e:
        print "full_clean_with_debugging threw %s" % e
        raise e
# patch(Model, 'full_clean', full_clean_with_debugging)

# Until https://code.djangoproject.com/ticket/16423#comment:3 is implemented,
# patch it in ourselves
def post_clean_with_simpler_validation(original_function, self):
    opts = self._meta
    # Update the model instance with self.cleaned_data.
    # print "construct_instance with password = %s" % self.cleaned_data.get('password')
    self.instance = construct_instance(self, self.instance, opts.fields, opts.exclude)
    # print "constructed instance with password = %s" % self.instance.password

    exclude = self._get_validation_exclusions()

    # Foreign Keys being used to represent inline relationships
    # are excluded from basic field value validation. This is for two
    # reasons: firstly, the value may not be supplied (#12507; the
    # case of providing new values to the admin); secondly the
    # object being referred to may not yet fully exist (#12749).
    # However, these fields *must* be included in uniqueness checks,
    # so this can't be part of _get_validation_exclusions().
    for f_name, field in self.fields.items():
        if isinstance(field, InlineForeignKeyField):
            exclude.append(f_name)

    # Clean the model instance's fields.
    try:
        self.instance.full_clean(exclude)
    except ValidationError, e:
        self._update_errors(e.update_error_dict(None))
patch(BaseModelForm, '_post_clean', post_clean_with_simpler_validation)

from django.forms import BaseForm
def clean_form_with_field_errors(original_function, self):
    try:
        self.cleaned_data = self.clean()
    except ValidationError, e:
        if hasattr(e, 'message_dict'):
            for field, error_strings in e.message_dict.items():
                self._errors[field] = self.error_class(error_strings)
        else:
            self._errors[NON_FIELD_ERRORS] = self.error_class(e.messages)
patch(BaseForm, '_clean_form', clean_form_with_field_errors)

from django.core.urlresolvers import RegexURLResolver, NoReverseMatch
from pprint import PrettyPrinter
pp = PrettyPrinter()
def reverse_with_debugging(original_function, self, lookup_view, *args, **kwargs):
    try:
        return original_function(self, lookup_view, *args, **kwargs)
    except NoReverseMatch as e:
        raise NoReverseMatch("%s (%s)" % (str(e),
            pp.pformat(self.reverse_dict)))
patch(RegexURLResolver, 'reverse', reverse_with_debugging)

from haystack.backends.whoosh_backend import WhooshSearchBackend, \
    AsyncWriter, SpellChecker
def update_with_extra_debugging(original_function, self, index, iterable,
    commit=True):
    if not self.setup_complete:
        self.setup()

    self.index = self.index.refresh()
    writer = AsyncWriter(self.index)

    for obj in iterable:
        doc = index.full_prepare(obj)

        # Really make sure it's unicode, because Whoosh won't have it any
        # other way.
        for key in doc:
            doc[key] = self._from_python(doc[key])

        try:
            writer.update_document(**doc)
        except Exception, e:
            if not self.silently_fail:
                raise

            self.log.error("Failed to add documents to Whoosh: %s (%s)" %
                (e, doc))

    if len(iterable) > 0:
        # For now, commit no matter what, as we run into locking issues otherwise.
        writer.commit()

        # If spelling support is desired, add to the dictionary.
        if self.include_spelling is True:
            sp = SpellChecker(self.storage)
            sp.add_field(self.index, self.content_field_name)
patch(WhooshSearchBackend, 'update', update_with_extra_debugging)

from whoosh.searching import Searcher
def search_without_optimisation(original_function, self, q, limit=10,
    sortedby=None, reverse=False, groupedby=None, optimize=True, filter=None,
    mask=None, terms=False, maptype=None):
    return original_function(self, q, limit, sortedby, reverse, groupedby,
        False, filter, mask, terms, maptype)
patch(Searcher, 'search', search_without_optimisation)

from django.contrib.admin.helpers import Fieldline, AdminField, mark_safe
from binder.admin import CustomAdminReadOnlyField
class FieldlineWithCustomReadOnlyField(object):
    def __init__(self, form, field, readonly_fields=None, model_admin=None):
        self.form = form # A django.forms.Form instance
        if not hasattr(field, "__iter__"):
            self.fields = [field]
        else:
            self.fields = field
        self.model_admin = model_admin
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    def __iter__(self):
        for i, field in enumerate(self.fields):
            if field in self.readonly_fields:
                yield CustomAdminReadOnlyField(self.form, field, is_first=(i == 0),
                    model_admin=self.model_admin)
            else:
                yield AdminField(self.form, field, is_first=(i == 0))

    def errors(self):
        return mark_safe(u'\n'.join([self.form[f].errors.as_ul() for f in self.fields if f not in self.readonly_fields]).strip('\n'))
import django.contrib.admin.helpers
django.contrib.admin.helpers.Fieldline = FieldlineWithCustomReadOnlyField

from django.db.backends.creation import BaseDatabaseCreation
def destroy_test_db_disabled(original_function, self, test_database_name,
    verbosity):
    pass
# patch(BaseDatabaseCreation, 'destroy_test_db', destroy_test_db_disabled)

# allow group lookups by name in fixtures, until
# https://code.djangoproject.com/ticket/13914 lands
from django.contrib.auth import models as auth_models
from django.db import models as db_models
class GroupManagerWithNaturalKey(db_models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)
# print "auth_models.Group.objects = %s" % auth_models.Group.objects
del auth_models.Group._default_manager
GroupManagerWithNaturalKey().contribute_to_class(auth_models.Group, 'objects')
def group_natural_key(self):
    return (self.name,)
auth_models.Group.natural_key = group_natural_key

import django.core.serializers.python
def Deserializer_with_debugging(original_function, object_list, **options):
    from django.core.serializers.python import _get_model
    from django.db import DEFAULT_DB_ALIAS
    from django.utils.encoding import smart_unicode
    from django.conf import settings

    print "loading all: %s" % object_list

    db = options.pop('using', DEFAULT_DB_ALIAS)
    db_models.get_apps()
    for d in object_list:
        print "loading %s" % d
        
        # Look up the model and starting build a dict of data for it.
        Model = _get_model(d["model"])
        data = {Model._meta.pk.attname : Model._meta.pk.to_python(d["pk"])}
        m2m_data = {}

        # Handle each field
        for (field_name, field_value) in d["fields"].iteritems():
            if isinstance(field_value, str):
                field_value = smart_unicode(field_value, options.get("encoding", settings.DEFAULT_CHARSET), strings_only=True)

            field = Model._meta.get_field(field_name)

            # Handle M2M relations
            if field.rel and isinstance(field.rel, db_models.ManyToManyRel):
                print "  field = %s" % field
                print "  field.rel = %s" % field.rel
                print "  field.rel.to = %s" % field.rel.to
                print "  field.rel.to._default_manager = %s" % (
                    field.rel.to._default_manager)
                print "  field.rel.to.objects = %s" % (
                    field.rel.to.objects)

                if hasattr(field.rel.to._default_manager, 'get_by_natural_key'):
                    def m2m_convert(value):
                        if hasattr(value, '__iter__'):
                            return field.rel.to._default_manager.db_manager(db).get_by_natural_key(*value).pk
                        else:
                            return smart_unicode(field.rel.to._meta.pk.to_python(value))
                else:
                    m2m_convert = lambda v: smart_unicode(field.rel.to._meta.pk.to_python(v))
                m2m_data[field.name] = [m2m_convert(pk) for pk in field_value]
                for i, pk in enumerate(field_value):
                    print "  %s: converted %s to %s" % (field.name,
                        pk, m2m_data[field.name][i])
    
    result = original_function(object_list, **options)
    print "  result = %s" % result
    import traceback
    traceback.print_stack()
    return result
# patch(django.core.serializers.python, 'Deserializer',
#     Deserializer_with_debugging)

import django.core.serializers.base
def save_with_debugging(original_function, self, save_m2m=True, using=None):
    print "%s.save(save_m2m=%s, using=%s)" % (self, save_m2m, using)
    original_function(self, save_m2m, using)
# patch(django.core.serializers.base.DeserializedObject, 'save',
#     save_with_debugging)

from django.test.utils import ContextList
def ContextList_keys(self):
    keys = set()
    for subcontext in self:
        for dict in subcontext:
            keys |= set(dict.keys())
    return keys
ContextList.keys = ContextList_keys

from haystack.backends.whoosh_backend import WhooshSearchBackend
def build_schema_with_debugging(original_function, self, fields):
    """
    print "build_schema fields = %s" % fields
    from haystack import connections
    
    unified = connections[self.connection_alias].get_unified_index()
    print "indexes = %s" % unified.indexes
    #        self.content_field_name, self.schema = self.build_schema(connections[self.connection_alias].get_unified_index().all_searchfields())
    print "collect_indexes = %s" % unified.collect_indexes()

    print "apps = %s" % settings.INSTALLED_APPS

    import inspect
    
    try:
        from django.utils import importlib
    except ImportError:
        from haystack.utils import importlib

    search_index_module = importlib.import_module("documents.search_indexes")
    for item_name, item in inspect.getmembers(search_index_module, inspect.isclass):
        print "%s: %s" % (item_name,
            getattr(item, 'haystack_use_for_indexing', False))

        if getattr(item, 'haystack_use_for_indexing', False):
            # We've got an index. Check if we should be ignoring it.
            class_path = "documents.search_indexes.%s" % (item_name)

            print "excluded_index %s = %s" % (class_path,
                class_path in unified.excluded_indexes)
            print "excluded_indexes_id %s = %s" % (str(item_name),
                unified.excluded_indexes_ids.get(item_name) == id(item))
    """
    from django.conf import settings
    print "build_schema: settings = %s" % settings
    print "build_schema: INSTALLED_APPS = %s" % settings.INSTALLED_APPS
    # import pdb; pdb.set_trace()
    return original_function(self, fields)
# patch(WhooshSearchBackend, 'build_schema', build_schema_with_debugging)

from haystack.utils.loading import UnifiedIndex
def build_with_debugging(original_function, self, indexes=None):
    print "UnifiedIndex build(%s)" % indexes
    import traceback
    traceback.print_stack()
    original_function(self, indexes)
    print "UnifiedIndex built: indexes = %s" % self.indexes
# patch(UnifiedIndex, 'build', build_with_debugging)

def collect_indexes_with_debugging(original_function, self):
    from django.conf import settings
    print "collect_indexes: settings = %s" % settings
    print "collect_indexes: INSTALLED_APPS = %s" % settings.INSTALLED_APPS
    # import pdb; pdb.set_trace()

    from haystack import connections
    from django.utils.module_loading import module_has_submodule
    import inspect
    
    try:
        from django.utils import importlib
    except ImportError:
        from haystack.utils import importlib

    for app in settings.INSTALLED_APPS:
        print "collect_indexes: trying %s" % app
        mod = importlib.import_module(app)

        try:
            search_index_module = importlib.import_module("%s.search_indexes" % app)
        except ImportError:
            if module_has_submodule(mod, 'search_indexes'):
                raise

            continue

        for item_name, item in inspect.getmembers(search_index_module, inspect.isclass):
            print "collect_indexes: %s: %s" % (item_name,
                getattr(item, 'haystack_use_for_indexing', False))
            if getattr(item, 'haystack_use_for_indexing', False):
                # We've got an index. Check if we should be ignoring it.
                class_path = "%s.search_indexes.%s" % (app, item_name)

                print "excluded_index %s = %s" % (class_path,
                    class_path in self.excluded_indexes)
                print "excluded_indexes_id %s = %s" % (str(item_name),
                    self.excluded_indexes_ids.get(item_name) == id(item))

                if class_path in self.excluded_indexes or self.excluded_indexes_ids.get(item_name) == id(item):
                    self.excluded_indexes_ids[str(item_name)] = id(item)
                    continue

    return original_function(self)
# patch(UnifiedIndex, 'collect_indexes', collect_indexes_with_debugging)

from django.conf import LazySettings
from django.conf import global_settings
def configure_with_debugging(original_function, self,
    default_settings=global_settings, **options):
    print "LazySettings configured: %s, %s" % (default_settings, options)
    import traceback
    traceback.print_stack()
    return original_function(self, default_settings, **options)
# patch(LazySettings, 'configure', configure_with_debugging)

def setup_with_debugging(original_function, self):
    print "LazySettings setup:"
    import traceback
    traceback.print_stack()
    return original_function(self)
# patch(LazySettings, '_setup', setup_with_debugging)

def before(target_class_or_module, target_method_name):
    # must return a decorator, i.e. a function that takes one arg,
    # which is the before_function, and returns a function (a wrapper)
    # that uses the before_function 
    original_function = getattr(target_class_or_module, target_method_name)
    def decorator(before_function):
        def wrapper_with_before(*args, **kwargs):
            before_function(*args, **kwargs)
            return original_function(*args, **kwargs)
        # only now do we have access to the before_function
        setattr(target_class_or_module, target_method_name, wrapper_with_before)
        return wrapper_with_before
    return decorator

def breakpoint(*args, **kwargs):
    import pdb; pdb.set_trace()
        
from django.contrib.admin.views.main import ChangeList
# before(ChangeList, 'get_results')(breakpoint)
# @before(ChangeList, 'get_results')
"""
def get_results_with_debugging(self, request):
    print "get_results query = %s" % object.__str__(self.query_set.query)
"""

def after(target_class_or_module, target_method_name):
    """
    This decorator generator takes two arguments, a class or module to
    patch, and the name of the method in that class (or function in that
    module) to patch.
    
    It returns a decorator, i.e. a function that can be called with a
    function as its argument (the after_function), and returns a function
    (the wrapper_with_after) that executes the original function/method and
    then the after_function.
    
    You can use this to monkey patch a class or method to execute arbitrary
    code after a method or function returns; the original return value
    is retained for you and you don't have to worry about it.
    """
       
    original_function = getattr(target_class_or_module, target_method_name)
    def decorator(after_function):
        def wrapper_with_after(*args, **kwargs):
            result = original_function(*args, **kwargs)
            after_function(*args, **kwargs)
            return result
        # only now do we have access to the after_function
        setattr(target_class_or_module, target_method_name, wrapper_with_after)
        return wrapper_with_after
    return decorator

# Work around https://github.com/toastdriven/django-haystack/issues/495 and
# http://south.aeracode.org/ticket/1023 by resetting the UnifiedIndex
# after South's syncdb has run
from south.management.commands.syncdb import Command as SouthSyncdbCommand
@after(SouthSyncdbCommand, 'handle_noargs')
def syncdb_handle_noargs_with_haystack_reset(self, migrate_all=False, **options):
    from haystack import connections
    for conn in connections.all():
        conn.get_unified_index().teardown_indexes()
        conn.get_unified_index().reset()
        conn.get_unified_index().setup_indexes()

def modify_return_value(target_class_or_module, target_method_name):
    """
    This decorator generator takes two arguments, a class or module to
    patch, and the name of the method in that class (or function in that
    module) to patch.
    
    It returns a decorator, i.e. a function that can be called with a
    function as its argument (the after_function), and returns a function
    (the wrapper_with_after) that executes the original function/method and
    then the after_function.
    
    You can use this to monkey patch a class or method to execute arbitrary
    code after a method or function returns. Your method is called with one
    additional parameter at the beginning, which is the return value of the
    original function; the value that you return becomes the new return value.
    """
       
    original_function = getattr(target_class_or_module, target_method_name)
    def decorator(after_function):
        def wrapper_with_after(*args, **kwargs):
            result = original_function(*args, **kwargs)
            result = after_function(result, *args, **kwargs)
            return result
        # only now do we have access to the after_function
        setattr(target_class_or_module, target_method_name, wrapper_with_after)
        return wrapper_with_after
    return decorator

# from haystack.indexes import RealTimeSearchIndex
# before(RealTimeSearchIndex, '_setup_save')(breakpoint)