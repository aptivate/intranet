from django import forms
from django.forms.widgets import SelectMultiple

from haystack import connections, connection_router
from haystack.backends import SQ, BaseSearchQuery
from haystack.constants import DEFAULT_ALIAS 
from haystack.forms import ModelSearchForm
from haystack.query import SearchQuerySet, AutoQuery
from haystack.fields import CharField
from haystack.views import SearchView

from binder.models import Program
from documents.models import DocumentType

haystack = connections[DEFAULT_ALIAS].get_unified_index()
all_fields = haystack.all_searchfields()
# print "unified index = %s" % haystack

class SearchQuerySetWithAllFields(SearchQuerySet):
    def __init__(self, site=None, query=None, fields=None):
        SearchQuerySet.__init__(self, site, query)
        
        if fields is None:
            """
            from haystack import connections, connection_router
            from haystack.constants import DEFAULT_ALIAS 
            index = connections[DEFAULT_ALIAS].get_unified_index()
            """
            fields = all_fields
        
        self.fields = fields
    
    """
    def _clone(self, klass=None):
        if klass is None:
            klass = self.__class__

        query = self.query._clone()
        clone = klass(site=self.site, query=query, fields=self.fields)
        clone._load_all = self._load_all
        return clone
    """

    def auto_query_custom(self, **kwargs):
        """
        Performs a best guess constructing the search query.

        This method is somewhat naive but works well enough for the simple,
        common cases.
        """
        return self.filter(**kwargs)
    
    def filter(self, **kwargs):
        print "enter filter: old query = %s" % self.query
        
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
        
        print "exit filter: new query = %s" % self.query
        return self

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
        kwargs['searchqueryset'] = SearchQuerySetWithAllFields()
        ModelSearchForm.__init__(self, *args, **kwargs)
        print "SearchFormWithAllFields initialised"

    def search(self):
        print "search starting"
        
        print "programs = %s" % self.cleaned_data.get("programs")
        
        if not self.is_valid():
            print "invalid form"
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
        
        return sqs.models(*self.get_models())

class SearchViewWithExtraFilters(SearchView):
    def extra_context(self):
        return {
            'is_real_search': (self.form.is_valid() and
                len(self.form.cleaned_data) > 0),
        }
