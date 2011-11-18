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

factors = [0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 2, 4, 8, 16, 32]

settings.MARXAN_NUMREPS = 3

MODE = 'hardcoded' 
#MODE = 'query' 
#MODE = 'create'

if MODE == 'query':
    wp = WatershedPrioritization.objects.filter(name__startswith="Auto Test Scale Factor")
    for w in wp:
        print "Querying", w.name, w
        scalefactors.append(w.input_scalefactor)
        r = w.results
        num_species.append(r['num_met'])
        num_units.append(r['num_units'])
        w.kml

if MODE == 'create':
    wp = WatershedPrioritization.objects.filter(name__startswith="Auto Test Scale Factor")
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
    scalefactors = [0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 2, 4, 8, 16, 32]
    num_units = [0, 3, 9, 17, 46, 57, 63, 73, 76, 79, 81, 82, 82, 83, 85, 90, 92, 93, 91]
    num_species = [0, 1, 4, 10, 27, 38, 37, 54, 57, 58, 63, 59, 62, 66, 66, 69, 71, 71, 71]



assert len(scalefactors) == len(num_species) == len(num_units)
print scalefactors
print num_units
print num_species

import matplotlib.pyplot as plt
fig = plt.figure()
plt.xlabel('Scale Factor')
plt.ylabel('Number of Species Goals Met')
ax = fig.add_subplot(111)
ax.scatter(scalefactors, num_species)
ax.set_xscale('log')
plt.show()
