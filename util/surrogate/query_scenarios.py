from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..', '..', 'priorities', __file__)))
import settings
setup_environ(settings)
#==================================#
from seak.models import Scenario
from django.contrib.auth.models import User
from django.utils import simplejson as json

import operator

user, created = User.objects.get_or_create(username='surrogate')

if __name__ == "__main__":
    scenarios = Scenario.objects.filter(user__username=user.username)

    sdict = {}

    for scen in scenarios:
        try:
            sdict[scen.id] = scen.results['surrogate']['objective_score']
        except:
            pass

    sorted_scenarios = sorted(sdict.items(), key=operator.itemgetter(1))
    print "Best 3 out of %d scenarios" % len(sorted_scenarios)
    for sid,sscore in sorted_scenarios[:3]:
        scen = Scenario.objects.get(id=sid)
        print
        print "Scenario", sid
        print "Targeted %s species" % scen.results['surrogate']['species_targeted']
        targets = [x['label'] for x in scen.results['targets_penalties'].values() if x['target'] > 0]
        for target in sorted(targets):
            print "\t",target
        print "Objective score %s" % scen.results['surrogate']['objective_score']
        missing = [x['name'] for x in scen.results['species'] if 0.25 < x['pcttotal'] < 0.50]
        print "Species not represented to the 50% level"
        for m in missing:
            print "\t", m
        missing = [x['name'] for x in scen.results['species'] if 0.00001 < x['pcttotal'] < 0.25]
        print "Species not represented to the 25% level"
        for m in missing:
            print "\t", m
        missing = [x['name'] for x in scen.results['species'] if x['pcttotal'] < 0.0000001]
        print "Missing these species entirely"
        for m in missing:
            print "\t", m

    print "\n====================\n common targets out of 500 top scenarios"
    all_targets = {}
    for sid,sscore in sorted_scenarios[:500]:
        scen = Scenario.objects.get(id=sid)
        targets = [x['label'] for x in scen.results['targets_penalties'].values() if x['target'] > 0]
        for target in targets:
            if target in all_targets.keys():
                all_targets[target] += 1
            else:
                all_targets[target] = 1

    all_targets = sorted(all_targets.items(), key=operator.itemgetter(1))
    for target, count in all_targets:
        print "%s,%s" % (count, target)
        



