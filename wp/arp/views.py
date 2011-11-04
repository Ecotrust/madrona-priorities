from lingcod.common import utils
from lingcod.shapes.views import ShpResponder
#from lingcod.features.views import get_object_for_viewing
from django.http import HttpResponse
from django.template.defaultfilters import slugify
import os
import json

def watershed_shapefile(request, instance):
    from arp.models import PlanningUnit, WatershedPrioritization
    viewable, response = instance.is_viewable(request.user)
    if not viewable:
        return response
    if not isinstance(instance, WatershedPrioritization):
        return HttpResponse("Shapefile export for watershed prioritizations only", status=500)

    ob = json.loads(instance.output_best)
    wids = [int(x.strip()) for x in ob['best']]
    puc = json.loads(instance.output_pu_count)
    wshds = PlanningUnit.objects.all()

#    from report.models import PlanningUnitShapes
#    for ws in wshds:
#        # create custom instances   
#        pus, created = PlanningUnitShapes.objects.get_or_create(puid=ws.pk, wpid=instance.pk)
#        if created or pus.date_modified < self.date_modified:
#            try:
#                hits = puc[str(ws.pk)] 
#            except:
#                hits = 0
#            best = ws.pk in wids
#            pus.name = self.name
#            pus.mpa_id_num = self.pk
#            pus.geometry = self.geometry_final
#            pus.save()

    if len(wshds) == 0:
        return HttpResponse( "Nothing in the query set; you don't want an empty shapefile", status=404)

    shp_response = ShpResponder(wshds)
    filename = slugify(instance.name) 
    shp_response.file_name = slugify(filename[0:8])
    return shp_response()

def watershed_marxan(request, instance):
    from arp.models import PlanningUnit, WatershedPrioritization
    viewable, response = instance.is_viewable(request.user)
    if not viewable:
        return response

    if not isinstance(instance, WatershedPrioritization):
        return HttpResponse("Shapefile export for watershed prioritizations only", status=500)

    from lingcod.common.utils import KMZUtil
    zu = KMZUtil()
    filename = os.path.join(tempfile.gettempdir(), '%s_%s.zip' % (slugify(instance.name),slugify(instance.date_modified)))
    directory = instance.outdir 
    zu.toZip(directory, filename)

    fh = open(filename,'rb')
    zip_stream = fh.read() 
    fh.close()
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=Marxan_%s.zip' % slugify(instance.name)
    response['Content-length'] = str(len(zip_stream))
    response['Content-Type'] = 'application/zip'
    response.write(zip_stream)
    return response

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
