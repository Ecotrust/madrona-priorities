from lingcod.common import utils
from lingcod.shapes.views import ShpResponder
#from lingcod.features.views import get_object_for_viewing
from django.http import HttpResponse
from django.template.defaultfilters import slugify

def watershed_shapefile(request, instance):
    from arp.models import Watershed, WatershedPrioritization

    viewable, response = instance.is_viewable(request.user)
    if not viewable:
        return response

    if not isinstance(instance, WatershedPrioritization):
        return HttpResponse("Shapefile export for watersheds only", status=500)

    filename = slugify(instance.name) 

    wids = [int(x.strip()) for x  in instance.output_units.split(',')]
    qs = Watershed.objects.filter(huc12__in=wids)
    if len(qs) == 0:
        return HttpResponse(
            "Nothing in the query set; you don't want an empty shapefile", 
            status=404
        )
    shp_response = ShpResponder(qs)
    shp_response.file_name = slugify(filename[0:8])
    return shp_response()
