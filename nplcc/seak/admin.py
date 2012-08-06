from seak.models import Folder, ConservationFeature, PlanningUnit, PuVsCf, PuVsCost, Cost
from django.contrib import admin

admin.site.register(Folder)
admin.site.register(ConservationFeature)
admin.site.register(PlanningUnit)
admin.site.register(Cost)
admin.site.register(PuVsCf)
admin.site.register(PuVsCost)

# Override flatblock admin
from flatblocks.models import FlatBlock
class FlatBlockAdmin(admin.ModelAdmin):
    ordering = ['slug', ]
    list_display = ('slug', 'content')
    search_fields = ('slug', 'content')

admin.site.unregister(FlatBlock)
admin.site.register(FlatBlock, FlatBlockAdmin)
