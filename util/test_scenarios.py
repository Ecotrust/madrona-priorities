from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..','nplcc',__file__)))

import settings
setup_environ(settings)
#==================================#
from seak.models import Scenario, ConservationFeature, PlanningUnit, Cost, PuVsCf, PuVsCost
from django.contrib.auth.models import User
from django.utils import simplejson as json
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
import time
import random

def mean(alist):
    floatNums = [float(x) for x in alist]
    return sum(floatNums) / len(alist)

user, created = User.objects.get_or_create(username='mperry')

scalefactors = []
num_species = []
num_units = []

factors = [2, 3, 4, 5]
#factors = [float(x)/20.0 for x in range(20,100)]
numspecies = [2,3,4]
numcosts = [2,1,3]
targets = [0.5, 0.25]
penalties = [0.5, 0.25]

settings.MARXAN_NUMREPS = 3

#MODE = 'hardcoded' 
#MODE = 'query' 
MODE = 'create'

if MODE == 'query':
    wp = Scenario.objects.filter(name__startswith="Test Scale Factor")
    for w in wp:
        print "Querying", w.name, w
        scalefactors.append(w.input_scalefactor)
        r = w.results
        num_species.append(r['num_met'])
        num_units.append(r['num_units'])
        w.kml

COUNT = 0

def create_wp(target_dict, penalties_dict, costs_dict, geography_list, sf):
    global COUNT
    COUNT += 1
    print target_dict
    print penalties_dict
    print costs_dict
    print geography_list
    print sf

    with open(os.path.join(os.path.dirname(__file__), 'random_words.txt'),'r') as fh:
        name = ' '.join([x.strip() for x in random.sample(fh.readlines(), 2)])

    name += " - %s" % sf

    wp = Scenario(input_targets = json.dumps( 
           target_dict
        ), 
        input_penalties = json.dumps(
            penalties_dict
        ), 
        input_relativecosts=json.dumps(
            costs_dict
        ), 
        input_geography=json.dumps(
            geography_list 
        ),
        input_scalefactor=sf,
        name= name, user=user)

    return wp


if MODE == 'create':
    wp = Scenario.objects.all() #filter(name__startswith="Auto Test Scale Factor")
    wp.delete()

    cfs =  ConservationFeature.objects.all()
    keys = []
    for c in cfs:
        a = c.level_string
        while a.endswith('---'):
            print a
            a = a[:-3]
        keys.append(a)

    fh = open("/home/mperry/results.csv", 'w+')
    fh.write('ncosts, nspecies, sumpenalties, meanpenalties, scalefactor, numspeciesmet, numplannningunits')
    fh.write('\n')
    fh.flush()

    g = GEOSGeometry('POINT(-13874668 %s)' % random.randrange(5005012, 8101549))
    for f in factors:
        for nc in numcosts:
            for n in numspecies:
                for i in range(1):
                    #if random.choice([True,False]):
                    geography_list = [x.fid for x in PlanningUnit.objects.filter(geometry__strictly_below=g)]
                    #else:
                    #geography_list = [x.fid for x in PlanningUnit.objects.filter(geometry__strictly_above=g)]

                    try:
                        n = int(n)
                        target_dict = {}
                        penalty_dict = {}
                        # pick n random species
                        selected_key = random.sample(keys, n) #'blah---blah'
                        if random.choice([True,False]):
                            t = random.choice(targets)
                            p = random.choice(penalties)
                        else:
                            t = None
                            p = None
                        for key in selected_key:
                            if t and p:
                                # Use the predetermined for ALL species
                                target_dict[key] = t 
                                penalty_dict[key] = p
                            else:
                                # random for each species
                                target_dict[key] = random.choice(targets)
                                penalty_dict[key] = random.choice(penalties)
                    except ValueError:
                        # ALL species
                        t = random.choice(targets)
                        p = random.choice(penalties)
                        t2 = random.choice(targets)
                        p2 = random.choice(penalties)
                        target_dict = { "coordinate":t, "uids":t2 } 
                        penalty_dict = { "coordinate":p, "uids":p2 } 

                    costs_dict = {} 
                    for a in random.sample([c.slug for c in Cost.objects.all()], nc):
                        costs_dict[a] = 1

                    sf = f
                    wp = create_wp(target_dict, penalty_dict, costs_dict, geography_list, sf)

                    print "####################################"
                    print 'targets', wp.input_targets
                    print 'penalties', wp.input_penalties
                    print 'costs', wp.input_relativecosts

                    wp.save()
                    #continue 
                    while not wp.done:
                        time.sleep(2)
                        print "  ", wp.status_html

                    inpenalties = json.loads(wp.input_penalties)

                    r = wp.results

                    #'ncosts, nspecies, sumpenalties, meanpenalties, scalefactor, numspeciesmet, numplannningunits'
                    fh.write(','.join([str(x) for x in [
                        sum(json.loads(wp.input_relativecosts).values()),
                        len(inpenalties.values()),
                        sum(inpenalties.values()),
                        mean(inpenalties.values()),
                        wp.input_scalefactor,
                        r['num_met'],
                        r['num_units']
                    ]]))
                    fh.write('\n')
                    fh.flush()

if MODE == 'hardcoded':
    scalefactors = [0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 2, 4, 8, 16, 32]
    num_units = [0, 3, 9, 17, 46, 57, 63, 73, 76, 79, 81, 82, 82, 83, 85, 90, 92, 93, 91]
    num_species = [0, 1, 4, 10, 27, 38, 37, 54, 57, 58, 63, 59, 62, 66, 66, 69, 71, 71, 71]

#import matplotlib.pyplot as plt
#fig = plt.figure()
#plt.xlabel('Scale Factor')
#plt.ylabel('Number of Species Goals Met')
#ax = fig.add_subplot(111)
#ax.scatter(scalefactors, num_species)
#ax.set_xscale('log')
#plt.show()
