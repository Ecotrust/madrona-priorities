#!/usr/bin/python
import random
import timeit

hucs = []
for i in range(40):
    hucs.append(random.randint(0,1000))

print len(hucs)
reps = 1000000

def run_randint():
    a = random.randint(0,39)
    h = hucs[a]

def run_random():
    a = int(random.random() * 40)
    if a == 0: print "got a zero!"
    if a == len(hucs): print "got one at len(hucs)"
    if a == len(hucs)-1: print "got one at len(hucs)-1"

    h = hucs[a]

def run_choice():
    h = random.choice(hucs)


if __name__ == '__main__':
        print timeit.Timer("run_randint()", "from __main__ import run_randint").timeit(number=reps)
        print timeit.Timer("run_random()", "from __main__ import run_random").timeit(number=reps)
        print timeit.Timer("run_choice()", "from __main__ import run_choice").timeit(number=reps)
