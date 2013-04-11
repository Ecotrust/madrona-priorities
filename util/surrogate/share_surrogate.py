from django.contrib.auth.models import User
from seak.models import Scenario

ids = [46748, 47448, 50170]

# Switch user
me = User.objects.get(username="mperry")
for i in ids:
    scenario = Scenario.objects.get(id=i)
    scenario.user = me
    scenario.save(rerun=False)

print "Go to application and share manually"
