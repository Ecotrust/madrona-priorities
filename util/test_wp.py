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

user = User.objects.get(username='mperry')

wp = WatershedPrioritization(input_targets = json.dumps( 
         {
             'widespread---trout': 0.5,
             'widespread---lamprey': 0.4,
             'widespread---salmon': 0.3,
             'widespread---steelhead': 0.2,
             'locally endemic': 0.1,
         } ), 
         input_penalties = json.dumps(
         {
             'widespread---trout': 50,
             'widespread---lamprey': 40,
             'widespread---salmon': 30,
             'widespread---steelhead': 20,
             'locally endemic': 10,
         } ), 
         input_relativecosts='[]', 
         name="Test", user=user)

wp.save()
print "--------------"
print wp.outdir
print "--------------"



