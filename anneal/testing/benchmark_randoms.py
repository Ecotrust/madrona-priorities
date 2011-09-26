#!/usr/bin/python
import random
import timeit

hucs = range(40)
print len(hucs)
reps = 1000000

def run_randint():
    a = random.randint(0,39)
    h = hucs[a]

def run_random():
    a = int(random.random() * 40)
    h = hucs[a]

def run_choice():
    h = random.choice(hucs)

from rand import c_random_int
def run_cython():
    a = c_random_int(40)
    h = hucs[a]

import numpy
def run_numpy():
    a = numpy.random.randint(40)
    h = hucs[a]


if __name__ == '__main__':
        print timeit.Timer("run_randint()", "from __main__ import run_randint").timeit(number=reps)
        print timeit.Timer("run_random()", "from __main__ import run_random").timeit(number=reps)
        print timeit.Timer("run_choice()", "from __main__ import run_choice").timeit(number=reps)
        print timeit.Timer("run_cython()", "from __main__ import run_cython").timeit(number=reps)
        print timeit.Timer("run_numpy()", "from __main__ import run_numpy").timeit(number=reps)
