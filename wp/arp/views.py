from lingcod.common import utils
from lingcod.shapes.views import ShpResponder
#from lingcod.features.views import get_object_for_viewing
from django.http import HttpResponse
from django.template.defaultfilters import slugify
import os

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

def test_params(request):
    from arp.models import WatershedPrioritization
    from django.contrib.auth.models import User
    from django.utils import simplejson as json
  
    if request.method == 'POST':
        user = User.objects.get(username='mperry')
        wp = WatershedPrioritization(input_targets = request.POST['input_targets'], 
                input_penalties = request.POST['input_penalties'],
                input_relativecosts='[]', 
                name="Test", user=user)
        wp.save()
        t = wp.process_dict(wp.input_targets)
        p = wp.process_dict(wp.input_penalties)
        a = json.dumps([t,p])
        res = HttpResponse(a, 200)
        res['Content-Type'] = 'application/json'
        return res
    else:
        return HttpResponse('POST required', status=404)
