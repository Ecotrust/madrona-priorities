from django import template
from django.utils.datastructures import SortedDict

register = template.Library()

def sort_by_cost_order(alist):
    new_list = []
    theorder = ['watershed-condition','climate','invasives']
    for k in theorder:
        if k in alist:
            new_list.append(k)
            alist.remove(k)
    for a in alist:
        new_list.append(a)
    new_list.reverse()
    return new_list

@register.filter(name='sortcosts')
def listsort(value):
  if isinstance(value,dict):
    new_dict = SortedDict()
    key_list = value.keys()
    new_list = sort_by_cost_order(key_list)
    for key in new_list:
      new_dict[key] = value[key]
    return new_dict
  elif isinstance(value, list):
    new_list = list(value)
    return sort_by_cost_order(new_list)
  else:
    return value
listsort.is_safe = True
