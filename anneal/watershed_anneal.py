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
penalties = { 'StlHd_m': 3000, 
            'Coho_m': 4000, 
            'Chnk_m': 5000 }
costs = ['pcp80bdfmm']
uidfield = 'OBJECTID'
#-----------------------------------------------#

def run():
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

    state = []
    for i in range(5): # To start off, pick 5 watersheds at random
        state.append(hucs[random.randint(num_hucs)])

    def reserve_move(state):
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

    totals = {}
    for s in species:
        totals[s] = 0

    def set_totals():

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
        e = 0
        for huc in state:
            watershed = watersheds[huc]
            if e == 0:
                for s in species:
                    totals[s] = watershed[s]
            else:
                for s in species:
                    totals[s] += watershed[s]

            for cost in costs:
                e += watershed[cost]

        # incorporate penalties for missing species targets
        for s in species:
            if totals[s] < targets[s]: 
                e += penalties[s]
        
        return e

    annealer = Annealer(reserve_energy, reserve_move)
    #Automatically chosen temperature schedule
    #state, e = annealer.auto(state, 4)
    """
    OR
     Manually chosen temperature schedule
    		state -- an initial arrangement of the system
    		Tmax -- maximum temperature (in units of energy)
    		Tmin -- minimum temperature (must be greater than zero)
    		steps -- the number of steps requested
    		updates -- the number of updates to print during annealing
    """
    state, e = annealer.anneal(state, 4500, 10, 3000 * len(hucs), 9)

    print "Reserve cost = %r" % reserve_energy(state)
    state.sort()
    for watershed in state:
        print "\t", watershed, watersheds[watershed]

if __name__ == "__main__":
    run()
