from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..','wp',__file__)))

import settings
setup_environ(settings)
#==================================#
from arp.models import WatershedPrioritization, ConservationFeature, PlanningUnit, Cost, PuVsCf, PuVsCost
from django.contrib.auth.models import User

user = User.objects.get(username='mperry')

wp = WatershedPrioritization(input_target= '[]', input_penalty='[]', input_relativecost='[]', name="Test", user=user)
wp.save()
print "--------------"
print wp.outdir
print "--------------"



