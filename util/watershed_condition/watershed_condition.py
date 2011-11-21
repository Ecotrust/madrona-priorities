import math
import sys
import os
from anneal import Annealer
import shapefile
import random

#-----------------------------------------------#
#-------------- Configuration ------------------#
#-----------------------------------------------#
shp = './data/HUC8_WC20111021.shp'
newshp = './outputs/out_sa15.shp'
#species = ['RD_DENS', 'FPDens10x', 'CropRatioX', 'd303x', 'rsx_x']
species = ['RoadDens', 'RdStrmInt', 'FrstPst', 'AvgPctImpv', 'Crops', 'Pasture', 'PopDens', 'WQ_NFHAP']



targets = {
            'RoadDens':46792, 
            'RdStrmInt':9744, 
            'FrstPst':377, 
            'AvgPctImpv':39446, 
            'Crops':1207, 
            'Pasture':1380, 
            'PopDens':1322734, 
            'WQ_NFHAP':259
           }
		  
penalties = {
            'RoadDens':5000, 
            'RdStrmInt':5000, 
            'FrstPst':5000, 
            'AvgPctImpv':5000, 
            'Crops':5000, 
            'Pasture':5000, 
            'PopDens':5000, 
            'WQ_NFHAP':5000
           }
           
costs = ['Sa_costs']
costscale = 5
uidfield = 'HUC_REF'
NUMREPS = 4
NUMITER = 500000

# Uncomment to manually define temperature schedule
#SCHEDULE = {'tmin': 10, 'tmax': 50, 'steps': 1}

#-----------------------------------------------#

watersheds = {}

def int2list(n, count=24):
    # returns a list with the binary digits of integer n,
    # using `count` number of digits
    return [int((n >> y) & 1) for y in range(count-1, -1, -1)]





def field_by_num(fieldname, fields):
    fnames = [x[0] for x in fields]
    return fnames.index(fieldname) - 1

print "Loading data from shapefile..."
sf = shapefile.Reader(shp)
fields = sf.fields
for rec in sf.records():
    skip = False
    vals = {}
    for s in species:
        vals[s] = rec[field_by_num(s, fields)]
    # precalc costs
    total_cost = 0
    for c in costs:
        fnum = field_by_num(c, fields)
        total_cost += float(rec[fnum]) * costscale

    vals['total_cost'] = total_cost

    if total_cost < 0.00001:
        skip = True

    if not skip:
        watersheds[int(rec[field_by_num(uidfield, fields)])] = vals

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
        Select random watershed
        then
        Add watershed (if not already in state) OR remove it. 
        * This is the Marxan technique as well
        """
        huc = random.choice(hucs)
        if huc in state:
            state.remove(huc)
        else:
            state.append(huc)

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
        # Initialize variables
        energy = 0
        totals = {}
        for fish in species:
            totals[fish] = 0

        # Get total cost and habitat in current state
        for huc in state:
            watershed = watersheds[huc]
            # Sum up total habitat for each fish
            for fish in species:
                if energy == 0:
                    # reset for new calcs ie first watershed
                    totals[fish] = float(watershed[fish])
                else:
                    # add for additional watersheds
                    totals[fish] += float(watershed[fish])

            # Incorporate Cost of including watershed
            energy += watershed['total_cost']

        # incorporate penalties for missing species targets
        
        for fish in species:
            if run_target[fish] > 0:
                pct = totals[fish] / run_target[fish]
            else:
                pct = 1
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
       print '----\nAutomatically determining optimal temperature schedule'
       schedule = annealer.auto(state, minutes=6)

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
    f = open('./data/output.txt', 'w')
    f.write('pu,frq\n')
    freq = {}
    states = []
    try:
        schedule = SCHEDULE
    except:
        schedule = None






# Example data ..
# code should be flexible enough to use real targets and species variables targets = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5} species = targets.keys()

######
# This is based on a binary mask concept # e.g. where  [0,1,1,1,1] is one possible target state # in which all but the first target is turned on.
    n = len(species) 
    masks = [] 
    for i in range(2**n):
        masks.append(int2list(i, n))

    
######
# Now we iterate through all possible 'masks'
# and multiply the mask by the original target set # result is a list of possible target dictionaries ###### 
        all_target_combos = [] 
        for mask in masks:
            assert len(species) == len(mask) #sanity check
            local_targets = {}
            for j in range(len(species)):
                s = species[j]
                m = mask[j]
                local_targets[s] = m * targets[s]
            all_target_combos.append(local_targets)

    for run_target in all_target_combos:
            # This is where you would run the simulated annealing against the run_target dictionary
        print run_target
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
        print "whatup"
    print 
    print "Frequency of hit (max of %s reps)..." % NUMREPS
    ks = freq.keys()
    ks.sort()
    w = shapefile.Writer(shapefile.POLYGON)
    w.field("HUC_REF", 'C', '10')
    w.field("NewReps", 'N', '12')
    w.field("RD_DENS", 'N', '12')
    orig = shapefile.Reader(shp)
    for k in ks:
        v = freq[k]
        print k, "#"*int(v), v
        ln_out = str(k) + "," + str(v) + "\n"
        f.write(ln_out)
        ids = k - 2 #this is a variable to sync up fid with huc_ref 
                    #because the reference in shapeRecord is for the FID.
        shapeRec = orig.shapeRecord(ids)
        print shapeRec.record[2]
        polyparts = shapeRec.shape.points
        w.poly(shapeType=3, parts=[polyparts])
        w.record(str(k),int(v),float(4.2))
		
    w.save(newshp)

    f.close()

