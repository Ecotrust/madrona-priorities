cython anneal.pyx
gcc -c -fPIC -I/usr/include/python2.7/ anneal.c
gcc -shared anneal.o -o anneal.so
