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

settings.MARXAN_NUMREPS = 3 # 7x less
settings.MARXAN_NUMITNS = 100000  # 10x less

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
    print "deleting scenarios for %s"  % user.username
    wp = Scenario.objects.filter(user__username=user.username)
    wp.delete()

    cfs =  ConservationFeature.objects.all()
    keys = []
    for c in cfs:
        a = c.level_string
        while a.endswith('---'):
            a = a[:-3]
        keys.append(a)

    for i in range(20):
        geography_list = [x.fid for x in PlanningUnit.objects.all()]

        target_dict = {}
        penalty_dict = {}
        n = random.randint(5,40)
        # pick n random species
        selected_keys = random.sample(keys, n) #'blah---blah'
        for key in keys:
            if key in selected_keys:
                target_dict[key] = 0.5
            else:
                target_dict[key] = 0
            penalty_dict[key] = 1.0

        costs_dict = {} 
        for a in [c.slug for c in Cost.objects.all()]:
            costs_dict[a] = 1

        scalefactor = 5
        print i 
        continue
        wp = create_wp(target_dict, penalty_dict, costs_dict, geography_list, scalefactor)
        wp.save()

        while not wp.done:
            time.sleep(0.333333)
            #print "  ", wp.status_html


        inpenalties = json.loads(wp.input_penalties)
        res = wp.results

        print "-----------------"
        print json.dumps(res['surrogate'], indent=2)
        print "..."

