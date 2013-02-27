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

user, created = User.objects.get_or_create(username='surrogate')

settings.MARXAN_NUMREPS = 2 # 7x less
settings.MARXAN_NUMITNS = 1000000  # 10x less

def create_wp(target_dict, penalties_dict, costs_dict, geography_list, sf):

    name = str(len([k for k,v in target_dict.items() if v > 0])) + ",".join(target_dict.keys())[:100]

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


if __name__ == "__main__":
    wp = Scenario.objects.filter(user__username=user.username)
    wp.delete()

    cfs =  ConservationFeature.objects.all()
    keys = []
    for c in cfs:
        a = c.level_string
        while a.endswith('---'):
            a = a[:-3]
        keys.append(a)

    geography_list = [x.fid for x in PlanningUnit.objects.all()]
    scalefactor = 5

    cost_groups = [
        (u'invasives', u'climate', u'watershed-condition-no-ais'),
        (u'invasives', u'watershed-condition-no-ais'),
        (u'climate', u'watershed-condition-no-ais'),
        (u'invasives', u'climate'),
        (u'watershed-condition-no-ais'),
        (u'invasives',),
        (u'climate',),
        ()
    ]

    results = []
    for selected_key in keys:
        for costs_on in cost_groups:
            costs_dict = {} 
            for a in [c.slug for c in Cost.objects.all()]:
                if a in costs_on:
                    costs_dict[a] = 1
                else:
                    costs_dict[a] = 0

            for t in range(10,110,10):
                target_dict = {}
                penalty_dict = {}

                for key in keys:
                    if key == selected_key:
                        target_dict[key] = float(t) / 100.0 
                    else:
                        target_dict[key] = 0
                    penalty_dict[key] = 1.0

                print selected_key, costs_on, t

                wp = create_wp(target_dict, penalty_dict, costs_dict, geography_list, scalefactor)
                wp.save()

                while not wp.done:
                    time.sleep(0.333333)

                inpenalties = json.loads(wp.input_penalties)
                res = wp.results

                results.append({'costs': costs_on, 'species': selected_key, 'target': t, 'surrogate': res['surrogate']})
                print results[-1]
                print "---------------------"

    with open("single1.json",'w') as fh:
        fh.write(json.dumps(results, indent=2))

