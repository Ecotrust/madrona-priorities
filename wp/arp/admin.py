from django.contrib.gis.db import models
from arp.models import *
from django.contrib import admin

admin.site.register(AOI)
admin.site.register(LOI)
admin.site.register(POI)
admin.site.register(Folder)
admin.site.register(UserKml)
admin.site.register(Watershed)
admin.site.register(WatershedPrioritization)
admin.site.register(BufferPoint)
