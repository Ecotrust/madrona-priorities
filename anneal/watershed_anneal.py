from numpy import random
import math
import sys
from anneal import Annealer
from django.contrib.gis.gdal import DataSource

#-----------------------------------------------#
#-------------- Configuration ------------------#
#-----------------------------------------------#
ds = DataSource('../media/staticmap/data/huc6_4326.shp')
species = ['StlHd_m', 'Coho_m', 'Chnk_m']
targets = { 'StlHd_m': 511000, 
            'Coho_m': 521000, 
            'Chnk_m': 551000 }
penalties = { 'StlHd_m': 300, 
            'Coho_m': 200, 
            'Chnk_m': 100 }
costs = ['pcp80bdfmm']
uidfield = 'OBJECTID'
#-----------------------------------------------#

def run(schedule=None):
    watersheds = {}
    for f in ds[0]:
        skip = False
        vals = {}
        for s in species:
            vals[s] = f.get(s)
        for c in costs:
            if float(f.get(c)) < 0.00001:
                skip = True
            vals[c] = f.get(c)

        if not skip:
            watersheds[f.get(uidfield)] = vals

    """
     At this point, the `watersheds`variable should be 
     a dictionary of watersheds
     where each watershed value is a dictionary of species and costs, eg
    
     {
      'HUC 171003030703': {'Chnk_m': 11223.5, 'StlHd_m': 12263.7, 'Coho_m': 11359.1}, 
      .....
     }
    """

    hucs = watersheds.keys()
    num_hucs = len(hucs)
    print num_hucs
    sys.exit()

    state = []
    for i in range(5): # To start off, pick 5 watersheds at random
        state.append(hucs[random.randint(num_hucs)])

    def old_reserve_move(state):
        """
        1st Random choice: Add new watershed OR remove an existing one
        then
        2nd Random choice: Which watershed to add or remove
        """
        #add_new = random.choice([True,False])
        add_new = random.randint(2)

        if add_new==1:
            # Append a new watershed to reserve
            if len(state) < num_hucs:
                # About 3x faster than ... h = random.choice(hucs)
                h = hucs[ random.randint(num_hucs)]
                while h in state: 
                    # keep going until we find one not already in the reserve
                    h = hucs[ random.randint(num_hucs)]
                state.append(h)
        else:
            # Remove an existing watershed from reserve
            lenstate = len(state)
            if lenstate > 1:
                h = state[ random.randint(lenstate)]
                state.remove(h)

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
        else:
            state.append(huc)

    totals = {}
    for s in species:
        totals[s] = 0

    #def set_totals():

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
        for huc in state:
            watershed = watersheds[huc]

            # Sum up total habitat for each fish
            for fish in species:
                if energy == 0:
                    totals[fish] = watershed[fish]
                else:
                    totals[fish] += watershed[fish]

            # Incorporate Cost of including watershed
            for cost in costs:
                energy += watershed[cost]

        # incorporate penalties for missing species targets
        for fish in species:
            if totals[fish] < targets[fish]: 
                pct = totals[fish] / targets[fish]
                # Avoid zerodivision errors 
                # Also limits the final penalty to 10x the specified penalty
                if pct < 0.1:
                    pct = 0.1
                penalty = int(penalties[fish] / pct)
                    
                #print "Missed target for", fish, "(", targets[fish], ")... only got", totals[fish]
                #print "   missed by", pct, ".... penalty is", penalty
                energy += penalty #penalties[fish]
        
        return energy

    annealer = Annealer(reserve_energy, reserve_move)
    if schedule is None:
       # Automatically chosen temperature schedule
       schedule = annealer.auto(state, minutes=0.3)

    """
    OR
     Manually chosen temperature schedule
    		state -- an initial arrangement of the system
    		Tmax -- maximum temperature (in units of energy)
    		Tmin -- minimum temperature (must be greater than zero)
    		steps -- the number of steps requested
    		updates -- the number of updates to print during annealing
    """
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
    schedule = None
    for i in range(4):
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
