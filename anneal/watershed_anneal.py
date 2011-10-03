import math
import sys
import os
from anneal import Annealer
from numpy import random

#-----------------------------------------------#
#-------------- Configuration ------------------#
#-----------------------------------------------#
shp = '../media/staticmap/data/huc6_4326.shp'
json_cache = './watersheds.json'
species = ['StlHd_m', 'Coho_m', 'Chnk_m']
targets = { 'StlHd_m': 511000, 
            'Coho_m': 521000, 
            'Chnk_m': 551000 }
penalties = { 'StlHd_m': 300, 
            'Coho_m': 200, 
            'Chnk_m': 100 }
costs = ['pcp80bdfmm']
uidfield = 'OBJECTID'
NUMREPS = 2 # 30
NUMITER = 50000 # 1 million
SCHEDULE = {'tmin': 10, 'tmax': 6500, 'steps': 1}
#-----------------------------------------------#

watersheds = {}
if os.path.exists(json_cache):
    print "Loading data from json..."
    import json
    fh = open(json_cache,'r')
    watersheds = json.loads(fh.read())
else:
    print "Loading data from shapefile..."
    from django.contrib.gis.gdal import DataSource
    ds = DataSource(shp)
    for f in ds[0]:
        skip = False
        vals = {}
        for s in species:
            vals[s] = f.get(s)
        # precalc costs
        total_cost = 0
        for c in costs:
            total_cost += float(f.get(c))
        vals['total_cost'] = total_cost

        if total_cost < 0.00001:
            skip = True

        if not skip:
            watersheds[int(f.get(uidfield))] = vals
        fh = open(json_cache, 'w')
        fh.write(json.dumps(watersheds))
        fh.close()

"""
    At this point, the `watersheds`variable should be 
    a dictionary of watersheds
    where each watershed value is a dictionary of species and costs, eg

    {
    171003030703: {'Chnk_m': 11223.5, 'StlHd_m': 12263.7, 'Coho_m': 11359.1, 'total_cost': 1234}, 
    .....
    }
"""
hucs = watersheds.keys()
num_hucs = len(hucs)

def run(schedule=None):
    state = []


    def reserve_move(state):
        """
        1st Random choice: Select watershed
        then
        Add watershed (if not already in state) OR remove it. 
        
        This is the Marxan method
        """
        huc = hucs[random.randint(num_hucs)]

        if huc in state:
            state.remove(huc)
            return ('r', huc)
        else:
            state.append(huc)
            return ('a', huc)

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
        totals = {}
        for huc in state:
            watershed = watersheds[huc]
            # Sum up total habitat for each fish
            for fish in species:
                if energy == 0:
                    # reset for new calcs
                    totals[fish] = watershed[fish]
                else:
                    totals[fish] += watershed[fish]

            # Incorporate Cost of including watershed
            energy += watershed['total_cost']

        # incorporate penalties for missing species targets
        for fish in species:
            pct = totals[fish] / targets[fish]
            if pct < 1.0: # if missed target, ie total < target
                if pct < 0.1:
                    # Avoid zerodivision errors 
                    # Limits the final to 10x specified penalty
                    pct = 0.1
                penalty = int(penalties[fish] / pct)
                energy += penalty 
        
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
                               schedule['steps'], updates=6)

    print "Reserve cost = %r" % reserve_energy(state)
    state.sort()
    for watershed in state:
        print "\t", watershed, watersheds[watershed]
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
