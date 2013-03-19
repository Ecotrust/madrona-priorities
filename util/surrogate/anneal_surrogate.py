from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.join('..', '..', 'priorities', __file__))))
import settings
setup_environ(settings)
#==================================#
from seak.models import Scenario, ConservationFeature, PlanningUnit, Cost
from madrona.async.ProcessHandler import process_is_complete
from django.contrib.auth.models import User
from django.utils import simplejson as json
import time
import random
from anneal import Annealer
import numpy as np
from datetime import datetime

#-----------------------------------------------#
#-------------- Configuration ------------------#
#-----------------------------------------------#
username = 'surrogate'
# set these in settings_local.py and `sudo service celeryd_usfw2 restart`
#settings.MARXAN_NUMREPS = 3
#settings.MARXAN_NUMITNS = 1000000

NUMREPS = 3
NUMITER = 20000

MAX_START_ENERGY = 60  # don't accept a random start until we're below this
SCHEDULE = {'tmin': 1, 'tmax': 25, 'steps': NUMITER}
#-----------------------------------------------#

user, created = User.objects.get_or_create(username=username)
wp = Scenario.objects.filter(user__username=username)
wp.delete()

geography_list = [x.fid for x in PlanningUnit.objects.all()]

costs_dict = {} 
for a in [c.slug for c in Cost.objects.all()]:
    if a in ['watershed-condition-no-ais', ' invasives', ' climate']:
        costs_dict[a] = 1
    else:
        costs_dict[a] = 0

cfs =  ConservationFeature.objects.all()
cfkeys = []
for c in cfs:
    a = c.level_string
    while a.endswith('---'):
        a = a[:-3]
    cfkeys.append(a)

num_cfs = len(cfkeys)

def run(schedule=None):

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
        start = datetime.now()

        target_dict = {}
        penalty_dict = {}
        for cfkey in cfkeys:
            if cfkey in state:
                target_dict[cfkey] = 0.5
            else:
                target_dict[cfkey] = 0

            penalty_dict[cfkey] = 1.0

        scalefactor = 5

        name = str(len([k for k,v in target_dict.items() if v > 0])) + ": " + " ".join([x.split("---")[1] for x in state])[:100]

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

        url = wp.get_absolute_url()
        time.sleep(3) # assuming it takes at least X secs
        while not process_is_complete(url):
            time.sleep(0.2)

        wp.process_results()
        res = wp.results
        energy = res['surrogate']['objective_score']

        elapsed = datetime.now() - start 

        print "Scenario %d\t\t%s secs\t\tscore = %s" % (wp.id, elapsed.seconds + elapsed.microseconds/1000000.0, energy)

        return energy

    # init
    init_species = [  # based on the single species chart, we know these are good starting points
        'locally-endemic---whitefish-mountain',
        'locally-endemic---dace-longnose',
        'widespread-trout---bull-trout',
    ]
    print init_species

    start_energy = 999999
    #while start_energy > MAX_START_ENERGY:
    while True:
        #numstart = random.randint(0, 10)
        #state = random.sample(cfkeys, numstart)
        state = []
        for initsp in init_species:
            if not initsp in state:
                state.append(initsp)
        start_energy = reserve_energy(state)

    print "Starting energy is ", start_energy

    annealer = Annealer(reserve_energy, reserve_move)

    print '---\nAnnealing from %.2f to %.2f over %i steps:' % (schedule['tmax'], 
            schedule['tmin'], schedule['steps'])

    state, e = annealer.anneal(state, schedule['tmax'], schedule['tmin'], 
                               schedule['steps'], updates=int(schedule['steps']/2.))

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

