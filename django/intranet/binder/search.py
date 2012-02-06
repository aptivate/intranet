from django.contrib.admin.templatetags import admin_list
 
from django import forms
from django.db import models as fields
from django.forms.widgets import SelectMultiple

from haystack import connections, connection_router
from haystack.backends import SQ, BaseSearchQuery
from haystack.constants import DEFAULT_ALIAS 
from haystack.fields import CharField
from haystack.forms import ModelSearchForm
from haystack.models import SearchResult
from haystack.query import SearchQuerySet, AutoQuery
from haystack.views import SearchView

from binder.models import Program
from documents.models import DocumentType

haystack = connections[DEFAULT_ALIAS].get_unified_index()
all_fields = haystack.all_searchfields()
# print "unified index = %s" % haystack

class SearchResultWithModelCompatibility(SearchResult):
    def serializable_value(self, field_name):
        print "%s.serializable_value(%s) = %s" % (self, field_name,
            getattr(self, field_name))
        return getattr(self, field_name)

class SearchQuerySetWithAllFields(SearchQuerySet):
    def __init__(self, site=None, query=None, fields=None, meta=None):
        SearchQuerySet.__init__(self, site, query)
        
        if fields is None:
            """
            from haystack import connections, connection_router
            from haystack.constants import DEFAULT_ALIAS 
            index = connections[DEFAULT_ALIAS].get_unified_index()
            """
            fields = all_fields
        
        self.fields = fields
        # import pdb; pdb.set_trace()

        print "sqs init (%s): meta = %s" % (self, meta)
        import traceback
        traceback.print_stack()
        
        class SearchResultWithMeta(SearchResultWithModelCompatibility):
            _meta = meta

            def _clone(self, klass=None):
                result = super(SearchQuerySet, self)._clone(klass)
                result._meta = meta
                print "clone (%s): set _meta to %s" % (self, meta)
                return result
        
        self.query.set_result_class(SearchResultWithMeta)
        
    def auto_query_custom(self, **kwargs):
        """
        Performs a best guess constructing the search query.

        This method is somewhat naive but works well enough for the simple,
        common cases.
        """
        return self.filter(**kwargs)
    
    def filter(self, **kwargs):
        # print "enter filter: old query = %s" % self.query
        
        for param_name, param_value in kwargs.iteritems():
            dj = BaseSearchQuery()
        
            if param_name == 'content': 
                print "fields = %s" % self.fields
                
                for field_name, field_object in self.fields.iteritems():
                    if isinstance(field_object, CharField):
                        this_query = {field_name: param_value}
                        dj.add_filter(SQ(**this_query), use_or=True)
            
                # result = self.__and__(dj)
                self.query.combine(dj, SQ.AND)

            elif getattr(param_value, '__iter__'):
                for possible_value in param_value:
                    this_query = {param_name: possible_value}
                    dj.add_filter(SQ(**this_query), use_or=True)

                self.query.combine(dj, SQ.AND)
            
            else:
                self.query.add_filter(SQ({param_name: param_value}))
        
        # print "exit filter: new query = %s" % self.query
        return self
    
    def order_by(self, *args):
        """Alters the order in which the results should appear."""
        result = super(SearchQuerySetWithAllFields, self).order_by(*args)
        result.query.select_related = self.query.select_related
        result.query.where = self.query.where
        return result

class SelectMultipleWithJquery(SelectMultiple):
    def __init__(self, attrs=None, choices=(), html_name=None):
        SelectMultiple.__init__(self, attrs=attrs, choices=choices)
        self.html_name = html_name
        
    def render(self, name, value, attrs=None, choices=()):
        if self.html_name:
            name = self.html_name

        return SelectMultiple.render(self, name, value, attrs=attrs, choices=choices)

    def value_from_datadict(self, data, files, name):
        if self.html_name:
            name = self.html_name

        v = SelectMultiple.value_from_datadict(self, data, files, name)
        print "SelectMultiple.value_from_datadict(%s, %s, %s, %s) = %s" % (
            self, data, files, name, v)
        return v

class SearchFormWithAllFields(ModelSearchForm):
    programs = forms.MultipleChoiceField(
        choices=[(p.id, p.name) for p in Program.objects.all()],
        widget=SelectMultipleWithJquery(html_name='id_programs[]'), 
        required=False)
    document_types = forms.MultipleChoiceField(
        choices=[(t.id, t.name) for t in DocumentType.objects.all()],
        widget=SelectMultipleWithJquery(html_name='id_document_types[]'), 
        required=False)
    
    def __init__(self, *args, **kwargs):
        if 'searchqueryset' not in kwargs:
            kwargs['searchqueryset'] = SearchQuerySetWithAllFields()
        ModelSearchForm.__init__(self, *args, **kwargs)
        # print "SearchFormWithAllFields initialised"

    def search(self):
        # print "search starting"
        # print "programs = %s" % self.cleaned_data.get("programs")
        
        if not self.is_valid():
            # print "invalid form"
            return self.no_query_found()
        
        kwargs = {}

        if self.cleaned_data.get('q'):
            kwargs['content'] = self.cleaned_data.get('q')

        if self.cleaned_data.get('programs'):
            kwargs['programs'] = self.cleaned_data.get('programs')
        
        if self.cleaned_data.get('document_types'):
            kwargs['document_type'] = self.cleaned_data.get('document_types')
            
        if not kwargs:
            return self.no_query_found()
    
        sqs = self.searchqueryset.auto_query_custom(**kwargs)
        
        if self.load_all:
            sqs = sqs.load_all()
            
        self.count = sqs.count()
        
        return sqs.models(*self.get_models())

from django.contrib.admin.views.main import ChangeList
class SearchList(ChangeList):
    def url_for_result(self, result):
        return result.object.get_absolute_url()

class SearchViewWithExtraFilters(SearchView):
    list_display = ('title', )
    ordering = ['-title']
    verbose_name = "search result"
    object_name = 'SearchViewWithExtraFilters'

    from django.core.paginator import Paginator
    paginator = Paginator

    fields = {
        'title': fields.TextField(),
    }
    
    from django.template import RequestContext
    
    def get_field(self, name):
        return self.fields[name]
    
    def get_field_by_name(self, name):
        return (self.fields[name],)

    def get_paginator(self, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)
    
    def __init__(self, template=None, load_all=True, form_class=None, 
        searchqueryset=None, context_class=RequestContext, 
        results_per_page=None):
        
        if form_class is None:
            form_class = SearchFormWithAllFields
            
        super(SearchViewWithExtraFilters, self).__init__(template,
            load_all, form_class, searchqueryset, context_class,
            results_per_page)
        
        # ChangeList only uses this for URL generation, which we override anyway
        self.pk = self
        self.pk.attname = 'id'
        self._meta = self
        
        # import pdb; pdb.set_trace()
        
        from django.forms.forms import pretty_name
        for name, field in self.fields.iteritems():
            if field.verbose_name is None:
                field.verbose_name = pretty_name(name)
            field.set_attributes_from_name(name)
    
    def queryset(self, request):
        queryset = self.form.searchqueryset
        # patch the object to make ChangeList happy with the WhooshSearchQuery
        queryset.query.select_related = None
        queryset.query.where = False
        # print "SearchViewWithExtraFilters returning query = %s" % (
        #     object.__str__(queryset.query))
        return queryset
    
    def extra_context(self):
        # print self.form.searchqueryset.count
        
        change_list = SearchList(request=self.request, model=self,
            list_display=self.list_display, list_display_links=(),
            list_filter=(), date_hierarchy=None, search_fields=(),
            list_select_related=False, list_per_page=100,
            list_editable=(), model_admin=self)
        change_list.formset = None
        
        return {
            'is_real_search': (self.form.is_valid() and
                len(self.form.cleaned_data) > 0),
            'count': getattr(self.form, 'count', None),
            'change_list': change_list,
            # 'result_headers': list(admin_list.result_headers(self)),
        }

    def build_form(self, form_kwargs=None):
        if form_kwargs is None:
            form_kwargs = {}
        if 'searchqueryset' not in form_kwargs:
            form_kwargs['searchqueryset'] = SearchQuerySetWithAllFields(meta=self)
        return super(SearchViewWithExtraFilters, self).build_form(form_kwargs)
