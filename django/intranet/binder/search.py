from haystack.query import SearchQuerySet
from haystack.forms import SearchForm
from haystack.backends import SQ, BaseSearchQuery

import haystack.sites

class SearchQuerySetWithAllFields(SearchQuerySet):
    def __init__(self, site=None, query=None, fields=None):
        SearchQuerySet.__init__(self, site, query)
        
        if fields is None:
            fields = self.site.all_searchfields()
        
        self.fields = fields
    
    def _clone(self, klass=None):
        if klass is None:
            klass = self.__class__

        query = self.query._clone()
        clone = klass(site=self.site, query=query, fields=self.fields)
        clone._load_all = self._load_all
        return clone
    
    def filter(self, **kwargs):
        print "enter filter: old query = %s" % self.query
        
        dj = BaseSearchQuery()
        
        if len(kwargs) == 1 and 'content' in kwargs:
            term = kwargs['content']
            
            print "fields = %s" % self.fields
            
            for field_name, field_object in self.fields.iteritems():
                this_query = {field_name: term}
                """
                if field_object.document:
                    this_query = {field_name: term}
                else:
                    this_query = {field_name: '*%s*' % term}
                """ 
                dj.add_filter(SQ(**this_query), use_or=True)
            
            # result = self.__and__(dj)
            self.query.combine(dj, SQ.AND)
            result = self 
        else:
            result = SearchQuerySet.filter(self, **kwargs)
        
        print "exit filter: new query = %s" % result.query
        return result

class SearchFormWithAllFields(SearchForm):
    def __init__(self, *args, **kwargs):
        kwargs['searchqueryset'] = SearchQuerySetWithAllFields()
        SearchForm.__init__(self, *args, **kwargs)
        print "SearchFormWithAllFields initialised"