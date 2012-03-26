from django.contrib.gis.db import models
from seak.models import *
from django.contrib import admin

admin.site.register(Folder)
admin.site.register(ConservationFeature)
admin.site.register(PlanningUnit)
admin.site.register(Cost)
admin.site.register(PuVsCf)
admin.site.register(PuVsCost)

