from anneal import anneal, auto
import numpy as np
import math
import sys
import os
import json
from django.contrib.gis.gdal import DataSource

shp = '../media/staticmap/data/huc6_4326.shp'
json_cache = './watersheds.json'
species = ['StlHd_m', 'Coho_m', 'Chnk_m']
target_list = [511000, 521000, 53100]
penalty_list = [300, 200, 100]
cost_fields = ['pcp80bdfmm']
uidfield = 'OBJECTID'
NUMREPS = 4 # 30
NUMITER = 50000 # 1 million
TMAX = 2555.0 
TMIN = 5.0



watersheds = {}
if os.path.exists(json_cache):
    print "Loading data from json..."
    fh = open(json_cache,'r')
    watersheds = json.loads(fh.read())
else:
    print "Loading data from shapefile..."
    ds = DataSource(shp)
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
            watersheds[int(f.get(uidfield))] = vals
        fh = open(json_cache, 'w')
        fh.write(json.dumps(watersheds))
        fh.close()

"""
    At this point, the `watersheds`variable should be 
    a dictionary of watersheds
    where each watershed value is a dictionary of species and costs, eg

    {
    171003030703: {'Chnk_m': 11223.5, 'StlHd_m': 12263.7, 'Coho_m': 11359.1}, 
    .....
    }
"""
hucs = watersheds.keys()
hist = {}
for h in hucs:
    hist[h] = 0

def run():
    # start off with rows as planning units 
    # and cols as features (maps to GIS data) 
    thelist = []
    costs_list = []
    for huc in hucs:
        punit_data = watersheds[huc]
        huclist = []
        for s in species:
            huclist.append(punit_data[s])
        thelist.append(huclist)
        huc_cost = 0
        for c in cost_fields:
            huc_cost += punit_data[c]
        costs_list.append( huc_cost )

    features = np.array( thelist, np.double)
    # then transpose so that we've got features as rows 
    features = features.transpose() 
    num_features, num_punits  = features.shape
    targets = np.array( target_list , np.double)
    penalties = np.array( penalty_list , np.double)
    costs = np.array(costs_list, np.double) #np.ones( (num_punits), np.float) * 100
    #print "\n--------\n".join(str(x) for x in [features, targets, penalties, costs])

    #state = np.random.randint(0,2,(num_punits,))
    #schedule = auto(state, features, targets, penalties, costs) 
    #print schedule
    #sys.exit()

    for i in range(NUMREPS):
        #state = np.zeros( (num_punits), np.int0)
        state = np.random.randint(0,2,(num_punits,))
        result = anneal(state, features, targets, penalties, costs, TMAX, TMIN, NUMITER) 
        chosen = [hucs[x] for x in np.flatnonzero(state).tolist()]
        chosen.sort()
        print chosen, result[1]
        for ch in chosen:
            hist[ch] += 1

    hists = hist.keys()
    hists.sort()
    for k in hists:
        v = hist[k]
        if v > 0:
            print k, "*"*v, v

run()
