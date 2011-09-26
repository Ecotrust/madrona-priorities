#!/usr/bin/python
import copy 

alist = [1,2,3]

a = [1,2,alist]
b = a[:]
c = a
d = copy.deepcopy(a)

print """
alist = [1,2,3]
a = [1,2,alist]
b = a[:]
c = a
d = copy.deepcopy(a)

"""

print a
print b
print c
print d


alist.append(4)
print
print "alist.append(4)"
print

print a
print b
print c
print d


