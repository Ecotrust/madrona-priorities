from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..','wp',__file__)))

import settings
setup_environ(settings)
#==================================#
from arp.models import WatershedPrioritization, ConservationFeature, PlanningUnit, Cost, PuVsCf, PuVsCost
from django.contrib.auth.models import User
from django.utils import simplejson as json
from django.conf import settings
import time

user = User.objects.get(username='mperry')

scalefactors = []
num_species = []
num_units = []

factors = [0.1, 0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 2, 4, 8, 16, 32]
factors = [x + 0.05 for x in factors]
factors = [0.175, 0.2, 0.225]

settings.MARXAN_NUMREPS = 3

#MODE = 'hardcoded' 
MODE = 'query' 
#MODE = 'create'

if MODE == 'query':
    wp = WatershedPrioritization.objects.filter(name__startswith="Auto Test Scale Factor")
    for w in wp:
        print "Querying", w.name, w
        scalefactors.append(w.input_scalefactor)
        r = w.results
        num_species.append(r['num_met'])
        num_units.append(r['num_units'])

if MODE == 'create':
    wp = WatershedPrioritization.objects.filter(name__startswith="Auto Test")
    wp.delete()

    for sf in factors:
        wp = WatershedPrioritization(input_targets = json.dumps( 
                {
                "locally-endemic":0.5,
                "widespread":0.5
                } 
            ), 
            input_penalties = json.dumps(
                {
                "locally-endemic":0.5,
                "widespread":0.5
                } 
            ), 
            input_relativecosts=json.dumps(
                {
                    "watershed-condition":1,
                    "invasives":1,
                    "climate":1
                } 
            ), 
            input_scalefactor=sf,
            name="Auto Test Scale Factor %s" % sf, user=user)

        wp.save()

        while not wp.done:
            print "  ", wp.status_html
            time.sleep(1)

        scalefactors.append(sf)
        r = wp.results
        num_species.append(r['num_met'])
        num_units.append(r['num_units'])

if MODE == 'hardcoded':
    import math
    scalefactors = [1.3, 0.25, 0.4, 1.55, 0.5, 0.1, 0.6, 0.7, 0.8, 0.9, 0.175, 0.2, 0.225, 1.0, 1.1, 1.25, 4.0, 1.5, 2.0, 8.0, 16.0, 32.0, 1.05, 1.15, 0.15, 0.65, 0.3, 0.45, 0.55, 0.75, 0.85, 0.95, 2.05, 4.05, 32.05, 8.05, 16.05]
    #scalefactors = [math.log(x) for x in scalefactors]
    num_units = [90, 17, 35, 90, 54, 3, 66, 76, 79, 82, 5, 9, 12, 86, 86, 89, 94, 90, 92, 97, 97, 97, 86, 89, 4, 69, 26, 44, 59, 78, 82, 83, 94, 96, 97, 98, 97]
    num_species = num_units


assert len(scalefactors) == len(num_species) == len(num_units)
print scalefactors
print num_units
print num_species

import matplotlib.pyplot as plt
fig = plt.figure()
plt.xlabel('Scale Factor')
plt.ylabel('Number of Selected Watersheds')
ax = fig.add_subplot(111)
ax.scatter(scalefactors, num_units)
ax.set_xscale('log')
plt.show()
