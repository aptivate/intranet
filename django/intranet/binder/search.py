from django.contrib.admin.templatetags import admin_list
 
from django import forms
from django.db import models as fields
from django.forms.widgets import SelectMultiple
from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe

from haystack import connections, connection_router
from haystack.backends import SQ, BaseSearchQuery
from haystack.constants import DEFAULT_ALIAS 
from haystack.fields import CharField
from haystack.forms import ModelSearchForm
from haystack.models import SearchResult
from haystack.query import SearchQuerySet, AutoQuery
from haystack.views import SearchView

from binder.models import Program, IntranetUser
from documents.models import DocumentType

import django_tables2 as tables

haystack = connections[DEFAULT_ALIAS].get_unified_index()
all_fields = haystack.all_searchfields()
# print "unified index = %s" % haystack

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

        # print "sqs init (%s): meta = %s" % (self, meta)
        # import traceback
        # traceback.print_stack()
        
        # self.query.set_result_class(SearchResultWithExtraFields)
        
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
        if 'searchqueryset' not in kwargs:
            kwargs['searchqueryset'] = SearchQuerySetWithAllFields()
        ModelSearchForm.__init__(self, *args, **kwargs)
        # print "SearchFormWithAllFields initialised"

    def search(self):
        print "search starting"
        print "programs = %s" % self.cleaned_data.get("programs")
        
        if not self.is_valid():
            print "invalid form"
            return None
        
        kwargs = {}

        if self.cleaned_data.get('q'):
            kwargs['content'] = self.cleaned_data.get('q')

        if self.cleaned_data.get('programs'):
            kwargs['programs'] = self.cleaned_data.get('programs')
        
        if self.cleaned_data.get('document_types'):
            kwargs['document_type'] = self.cleaned_data.get('document_types')
            
        if not kwargs:
            print "no search"
            return None
    
        sqs = self.searchqueryset.auto_query_custom(**kwargs)
        
        if self.load_all:
            sqs = sqs.load_all()
            
        self.count = sqs.count()
        
        return sqs.models(*self.get_models())

from django.contrib.admin.views.main import ChangeList
class SearchList(ChangeList):
    def url_for_result(self, result):
        return result.object.get_absolute_url()

class SearchTable(tables.Table):
    title = tables.Column(verbose_name="Title")
    authors = tables.Column(verbose_name="Authors")
    created = tables.Column(verbose_name="Date Added")
    programs = tables.Column(verbose_name="Programs")
    document_type = tables.Column(verbose_name="Document Type")
    score = tables.Column(verbose_name="Score")
    
    def render_title(self, value, record):
        print "record = %s (%s)" % (record, dir(record))
        return mark_safe("<a href='%s'>%s</a>" % (record.object.get_absolute_url(),
            value))

    def render_authors(self, value):
        users = IntranetUser.objects.in_bulk(value)
        return ', '.join([users[long(i)].full_name for i in value])
    
    def render_programs(self, value):
        programs = Program.objects.in_bulk(value)
        return ', '.join([programs[long(i)].name for i in value])
    
    def render_document_type(self, value):
        return DocumentType.objects.get(id=value).name
    
    class Meta:
        attrs = {'class': 'paleblue'}
            
class SearchViewWithExtraFilters(SearchView):
    prefix = 'results_'
    page_field = 'page'

    from django.template import RequestContext
    
    def __init__(self, template=None, load_all=True, 
        form_class=SearchFormWithAllFields,
        searchqueryset=None, context_class=RequestContext,
        results_per_page=None):
        
        super(SearchViewWithExtraFilters, self).__init__(template, load_all,
            form_class, searchqueryset, context_class, results_per_page)

    def create_response(self):
        if self.results is None:
            return render_to_response(self.template, dict(form=self.form),
                context_instance=self.context_class(self.request))
        else:
            return super(SearchViewWithExtraFilters, self).create_response() 

    def extra_context(self):
        results_table = SearchTable(self.form.searchqueryset,
            prefix=self.prefix, page_field=self.page_field)
        current_page = self.request.GET.get(results_table.prefixed_page_field, 1)
        results_table.paginate(page=current_page)
        
        return {
            'is_real_search': (self.form.is_valid() and
                len(self.form.cleaned_data) > 0),
            'count': getattr(self.form, 'count', None),
            'results_table': results_table,
            'request': self.request,
            # 'result_headers': list(admin_list.result_headers(self)),
        }
