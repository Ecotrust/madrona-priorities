from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..', '..', 'priorities', __file__)))
import settings
setup_environ(settings)
#==================================#
from seak.models import Scenario, ConservationFeature, PlanningUnit, Cost
from django.contrib.auth.models import User
from django.utils import simplejson as json
from django.conf import settings
import time
import random
from anneal import Annealer
import numpy as np

user, created = User.objects.get_or_create(username='mperry')

settings.MARXAN_NUMREPS = 3
settings.MARXAN_NUMITNS = 100000

#-----------------------------------------------#
#-------------- Configuration ------------------#
#-----------------------------------------------#
NUMREPS = 30
NUMITER = 200
SCHEDULE = {'tmin': 1, 'tmax': 1000, 'steps': 20}
#SCHEDULE = None
#-----------------------------------------------#

geography_list = [x.fid for x in PlanningUnit.objects.all()]

costs_dict = {} 
for a in [c.slug for c in Cost.objects.all()]:
    costs_dict[a] = 1


cfs =  ConservationFeature.objects.all()
cfkeys = []
for c in cfs:
    a = c.level_string
    while a.endswith('---'):
        a = a[:-3]
    cfkeys.append(a)

num_cfs = len(cfkeys)

def run(schedule=None):
    numstart = random.randint(10, 40)
    state = random.sample(cfkeys, numstart)

    def reserve_move(state):
        """
        1st Random choice: Select watershed
        then
        Add watershed (if not already in state) OR remove it. 
        
        This is the Marxan method
        """
        cfkey = cfkeys[np.random.randint(num_cfs)]

        if cfkey in state:
            state.remove(cfkey)
            return ('r', cfkey)
        else:
            state.append(cfkey)
            return ('a', cfkey)

    def reserve_energy(state):
        """
        The "Objective Function"...
        Calculates the 'energy' of the reserve.
        Should incorporate costs of reserve and penalties 
        for not meeting species targets. 

        Note: This example is extremely simplistic compared to 
        the Marxan objective function (see Appendix B in Marxan manual)
        but at least we have access to it!
        """
        energy = 0

        target_dict = {}
        penalty_dict = {}
        for cfkey in cfkeys:
            if cfkey in state:
                target_dict[cfkey] = 0.5
            else:
                target_dict[cfkey] = 0

            penalty_dict[cfkey] = 1.0

        scalefactor = 5

        name = str(len([k for k,v in target_dict.items() if v > 0])) + ",".join(target_dict.keys())[:100]

        wp = Scenario(
            input_targets = json.dumps( 
                target_dict
            ), 
            input_penalties = json.dumps(
                penalty_dict
            ), 
            input_relativecosts=json.dumps(
                costs_dict
            ), 
            input_geography=json.dumps(
                geography_list 
            ),
            input_scalefactor=scalefactor,
            name= name, 
            user=user
        )
        wp.save()

        while not wp.done:
            time.sleep(0.333333)

        res = wp.results
        energy = res['surrogate']['objective_score']

        print "-----------------"
        print json.dumps(res['surrogate'], indent=2)
        print "..."

        return energy

    annealer = Annealer(reserve_energy, reserve_move)
    if schedule is None:
       # Automatically chosen temperature schedule
       schedule = annealer.auto(state, minutes=0.3)

    try:
        schedule['steps'] = NUMITER
    except:
        pass # just keep the auto one

    print '---\nAnnealing from %.2f to %.2f over %i steps:' % (schedule['tmax'], 
            schedule['tmin'], schedule['steps'])

    state, e = annealer.anneal(state, schedule['tmax'], schedule['tmin'], 
                               schedule['steps'], updates=schedule['steps'])

    print "Reserve cost = %r" % reserve_energy(state)
    state.sort()
    for key in state:
        print "\t", key
    return state, reserve_energy(state), schedule

if __name__ == "__main__":
    freq = {}
    states = []
    try:
        schedule = SCHEDULE
    except:
        schedule = None
    for i in range(NUMREPS):
        state, energy, schedule = run(schedule)
        states.append((state, energy))
        for w in state:
            if freq.has_key(w):
                freq[w] += 1
            else:
                freq[w] = 1

    print 
    print "States"
    for s in states:
        print s
    print 
    print "Frequency..."
    ks = freq.keys()
    ks.sort()
    for k in ks:
        v = freq[k]
        print k, "#"*int(v), v

