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