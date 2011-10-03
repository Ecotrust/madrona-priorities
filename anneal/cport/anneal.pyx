#!/usr/bin/env python

# Python module for simulated annealing - anneal.py - v1.0 - 2 Sep 2009
# 
# Copyright (c) 2009, Richard J. Wagner <wagnerr@umich.edu>
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
This module performs simulated annealing to find a state of a system that
minimizes its energy.

An example program demonstrates simulated annealing with a traveling
salesman problem to find the shortest route to visit the twenty largest
cities in the United States.

Notes:
    Matt Perry 6/24 : Changed to slicing lists instead of deepcopy-ing them.
                      e.g. state = prevState[:] instead of state = deepcopy(prevState)
                      Huge performance enhancement (~5-10x faster)
                      Should be identical behavior if the items in the state list are immutable.
                      (immutable objects include integers and strings so should be safe)
"""

# How to optimize a system with simulated annealing:
# 
# 1) Define a format for describing the state of the system.
# 
# 2) Define a function to calculate the energy of a state.
# 
# 3) Define a function to make a random change to a state.
# 
# 4) Choose a maximum temperature, minimum temperature, and number of steps.
# 
# 5) Set the annealer to work with your state and functions.
# 
# 6) Study the variation in energy with temperature and duration to find a
# productive annealing schedule.
# 
# Or,
# 
# 4) Run the automatic annealer which will attempt to choose reasonable values
# for maximum and minimum temperatures and then anneal for the allotted time.

import sys, time, math
import numpy as np
cimport numpy as np
#np.import_array()

DTYPE = np.double
ITYPE = np.int
# "ctypedef" assigns a corresponding compile-time type to DTYPE_t. For
# every type in the numpy module there's a corresponding compile-time
# type with a _t-suffix.
ctypedef np.double_t DTYPE_t
ctypedef np.int_t ITYPE_t

# The builtin min and max functions works with Python objects, and are
# so very slow. So we create our own.
#  - "cdef" declares a function which has much less overhead than a normal
#    def function (but it is not Python-callable)
#  - "inline" is passed on to the C compiler which may inline the functions
#  - The C type "int" is chosen as return type and argument types
#  - Cython allows some newer Python constructs like "a if x else b", but
#    the resulting C file compiles with Python 2.3 through to Python 3.0 beta.
#cdef inline int int_max(int a, int b): return a if a >= b else b
#cdef inline int int_min(int a, int b): return a if a <= b else b

cdef extern from "math.h":
    double ceil(double)
    double log10(double)
    double log(double)
    double fabs(double)
    double exp(double)

cdef move(np.ndarray[ITYPE_t, ndim=1] state):
    """
    Selects a planning unit at random and change it's status
    """
    # Note: edits the state array IN PLACE, nothing to return
    cdef int x
    x = np.random.randint(state.size)
    if state[x] == 1:
        state[x] = 0
    else:
        state[x] = 1

cdef double energy(np.ndarray[ITYPE_t, ndim=1] state, 
            np.ndarray[DTYPE_t, ndim=2] features, 
            np.ndarray[DTYPE_t, ndim=1] targets, 
            np.ndarray[DTYPE_t, ndim=1] penalties, 
            np.ndarray[DTYPE_t, ndim=1] costs):
    """ 
    The objective function
    Calculates costs and penalties for the scenario state
    """
    cdef np.ndarray[DTYPE_t, ndim=1] scenario_costs
    cdef np.ndarray[ITYPE_t, ndim=2] state_tile
    cdef np.ndarray[DTYPE_t, ndim=2] scenario_features
    cdef np.ndarray[DTYPE_t, ndim=1] feature_totals
    cdef np.ndarray[np.int8_t, ndim=1, cast=True] missed_target
    cdef np.ndarray[DTYPE_t, ndim=1] pcts
    cdef np.ndarray[DTYPE_t, ndim=1] feature_penalties
    cdef int num_features
    cdef int num_punits
    cdef double energy

    # Create array of costs of including the planning units
    # punits not in state -> zero
    scenario_costs = costs * state 

    # Create array with values for each planning unit
    #  and each conservation feature 
    num_features = features.shape[0]
    num_punits = features.shape[1]
    state_tile = np.tile(state, (num_features, 1))
    scenario_features = state_tile * features

    # Sum values across all planning units
    # Yields the total value of each conservation feature in this scenario
    feature_totals = np.sum(scenario_features, axis=1)

    # Include penalties for missed targets

    missed_target = feature_totals < targets
    pcts = (feature_totals+0.1) / targets
    feature_penalties = (penalties / pcts) * missed_target

    # Sum the costs + penalties to get the total "energy" of the scenario
    energy = scenario_costs.sum() + feature_penalties.sum()

    return energy

cpdef np.ndarray[ITYPE_t, ndim=1] anneal(np.ndarray[ITYPE_t, ndim=1] state, 
            np.ndarray[DTYPE_t, ndim=2] features, 
            np.ndarray[DTYPE_t, ndim=1] targets, 
            np.ndarray[DTYPE_t, ndim=1] penalties, 
            np.ndarray[DTYPE_t, ndim=1] costs,
            double Tmax, double Tmin, int steps):
    cdef int step = 0
    cdef int steps_since_update = 1
    cdef int update = 5000
    cdef double T
    cdef double Tfactor
    cdef double E
    cdef double dE
    cdef double prevEnergy
    cdef double bestEnergy
    cdef int trials 
    cdef int accepts
    cdef int improves
    cdef int do_update
    cdef np.ndarray[ITYPE_t, ndim=1] prevState
    cdef np.ndarray[ITYPE_t, ndim=1] bestState

    # Precompute factor for exponential cooling from Tmax to Tmin
    if Tmin <= 0.0:
        print 'Exponential cooling requires a minimum temperature greater than zero.'
        sys.exit()
    Tfactor = -1 * log( Tmax / Tmin )
    
    # Note initial state
    T = Tmax
    E = energy(state, features, targets, penalties, costs)
    prevState = state.copy()
    prevEnergy = E
    bestState = state.copy()
    bestEnergy = E
    trials, accepts, improves = 0, 0, 0
    do_update = 0
    
    # Attempt moves to new states
    while step < steps:
        step += 1
        steps_since_update += 1

        if update and (step % update == 0 or step == 1):
            do_update = 1
            print "Step", step

        T = Tmax * exp( Tfactor * step / steps )
        move(state)
        E = energy(state, features, targets, penalties, costs)
        dE = E - prevEnergy
        trials += 1

        if do_update:
            print "  temp =", int(T), "energy=", int(E), "number of watersheds=", state.sum()

        if dE > 0.0 and exp(-dE/T) < np.random.random():
            # Restore previous state
            state = prevState.copy()
            E = prevEnergy
        else:
            # Accept new state and compare to best state
            accepts += 1
            if dE < 0.0:
                improves += 1
            prevState = state.copy()
            prevEnergy = E
            if E < bestEnergy:
                bestState = state.copy()
                bestEnergy = E

        if do_update:
            print "  accepts =", int(float(accepts)*100/steps_since_update), "%  improves=", int(float(improves)*100/steps_since_update),"%"
            do_update = 0
            steps_since_update = 1
            accepts = 0
            improves = 0
    
    return bestState

def auto(state, features, targets, penalties, costs, minutes=1, steps=2000):
    def run(state, T, steps):
        E = energy(state, features, targets, penalties, costs)
        prevState = state.copy()
        prevEnergy = E
        accepts, improves = 0, 0
        for step in range(steps):
            move(state)
            E = energy(state, features, targets, penalties, costs)
            dE = E - prevEnergy
            if dE > 0.0 and math.exp(-dE/T) < np.random.random():
                state = prevState.copy()
                E = prevEnergy
            else:
                accepts += 1
                if dE < 0.0:
                    improves += 1
                prevState = state.copy()
                prevEnergy = E
        return state, E, float(accepts)/steps, float(improves)/steps
    
    step = 0
    start = time.time()
    
    print 'Attempting automatic simulated anneal...'
    
    # Find an initial guess for temperature
    T = 0.0
    E = energy(state, features, targets, penalties, costs)
    while T == 0.0:
        step += 1
        move(state)
        T = abs( energy(state, features, targets, penalties, costs) - E )
        print T, step

    print T
    
    print 'Exploring temperature landscape:'
    print ' Temperature        Energy    Accept   Improve     Elapsed'
    def update(T, E, acceptance, improvement):
        """Prints the current temperature, energy, acceptance rate,
        improvement rate, and elapsed time."""
        elapsed = time.time() - start
        print '%12.2f  %12.2f  %7.2f%%  %7.2f%%  %s' % \
            (T, E, 100.0*acceptance, 100.0*improvement, elapsed)
    
    # Search for Tmax - a temperature that gives 98% acceptance
    state, E, acceptance, improvement = run(state, T, steps)
    step += steps
    while acceptance > 0.98:
        T = T/1.5
        state, E, acceptance, improvement = run(state, T, steps)
        step += steps
        update(T, E, acceptance, improvement)
    while acceptance < 0.98:
        T = T*1.5
        state, E, acceptance, improvement = run(state, T, steps)
        step += steps
        update(T, E, acceptance, improvement)
    Tmax = T
    
    # Search for Tmin - a temperature that gives 0% improvement
    while improvement > 0.0:
        T = T/1.5
        state, E, acceptance, improvement = run(state, T, steps)
        step += steps
        update(T, E, acceptance, improvement)
    Tmin = T
    
    # Calculate anneal duration
    elapsed = time.time() - start
    duration = int(60.0 * minutes * step / elapsed)
    
    # MP: Don't perform anneal, just return params
    #return self.anneal(state, Tmax, Tmin, duration, 20)
    return {'tmax': Tmax, 'tmin': Tmin, 'steps': duration}
