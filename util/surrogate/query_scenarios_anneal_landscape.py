from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..', '..', 'priorities', __file__)))
import settings
setup_environ(settings)
#==================================#
from seak.models import Scenario
from django.contrib.auth.models import User

user, created = User.objects.get_or_create(username='surrogate')

if __name__ == "__main__":
    scenarios = Scenario.objects.filter(user__username=user.username)
    print "id,score"
    for scen in scenarios:
        try:
            print "%s,%s" % (scen.id, scen.results['surrogate']['objective_score'])
        except:
            pass
