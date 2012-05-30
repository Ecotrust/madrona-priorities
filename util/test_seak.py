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

user = User.objects.get(username='mperry')

wp = Scenario(input_targets = json.dumps( 
         {
             'coordinate': 0.2,
             'uids': 0.1,
         } ), 
         input_penalties = json.dumps(
         {
             'coordinate': 20,
             'uids': 10,
         } ), 
         input_relativecosts='[]', 
         name="Test", user=user)

wp.save()
print "--------------"
print wp.outdir
print "--------------"



