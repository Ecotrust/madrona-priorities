from madrona.common import utils
from madrona.common.utils import load_session, get_logger
from madrona.shapes.views import ShpResponder
#from madrona.features.views import get_object_for_viewing
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import MultiPolygon
from django.shortcuts import render_to_response
from django.core.cache import cache
from django.conf import settings
from django.template import RequestContext
from seak.models import PlanningUnit
import os
import json
import time
import tempfile

logger = get_logger()

def map(request, template_name='common/map_ext.html', extra_context={}):
    """
    Main application window
    """
    context = RequestContext(request,{
        'api_key':settings.GOOGLE_API_KEY, 
        'session_key': request.session.session_key,
    })
    context.update(extra_context)
    return render_to_response(template_name, context)

def watershed_shapefile(request, instances):
    from seak.models import PlanningUnit
    wshds = PlanningUnit.objects.all()
    stamp = int(time.time() * 1000.0)

    for instance in instances:
        viewable, response = instance.is_viewable(request.user)
        if not viewable:
            return response
        if not isinstance(instance, WatershedPrioritization):
            return HttpResponse("Shapefile export for watershed prioritizations only", status=500)

        ob = json.loads(instance.output_best)
        wids = [int(x.strip()) for x in ob['best']]
        puc = json.loads(instance.output_pu_count)

        for ws in wshds:
            # create custom model records
            pus, created = PlanningUnitShapes.objects.get_or_create(pu=ws, stamp=stamp)

            # Only do this on the first go 'round
            if created and not pus.geometry:
                pus.name = ws.name
                pus.fid = ws.fid
                p = ws.geometry.simplify(100)
                if p.geom_type == 'Polygon':
                    pus.geometry = MultiPolygon(p)
                elif p.geom_type == 'MultiPolygon':
                    pus.geometry = p

            # Calculate hits and best
            try:
                hits = puc[str(ws.pk)] 
            except:
                hits = 0
            best = ws.pk in wids
            pus.hits += hits
            if best:
                pus.bests += 1
            pus.save()

    readme = """Watershed Prioritization Analysis
contact: mperry@ecotrust.org

Includes scenarios:
    %s

Contains HUC8s from Oregon, Washington, Idaho
    'bests' contains the number of scenarios in which the subbasin was included in the best run
    'hits' contains the number of times the subbasin was included in any run, cumulative across scenarios.
    """ % ('\n    '.join([i.name for i in instances]), )

    allpus = PlanningUnitShapes.objects.filter(stamp=stamp)
    shp_response = ShpResponder(allpus, readme=readme)
    filename = '_'.join([slugify(i.pk) for i in instances])
    shp_response.file_name = slugify('nplcc_' + filename)
    return shp_response()

def watershed_marxan(request, instance):
    from seak.models import PlanningUnit, WatershedPrioritization
    viewable, response = instance.is_viewable(request.user)
    if not viewable:
        return response

    if not isinstance(instance, WatershedPrioritization):
        return HttpResponse("Shapefile export for watershed prioritizations only", status=500)

    from madrona.common.utils import KMZUtil
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
    from seak.models import WatershedPrioritization
    from django.contrib.auth.models import User
    from django.utils import simplejson as json
  
    if request.method == 'POST':
        user = User.objects.get(username='mperry')
        nplcc = WatershedPrioritization(input_targets = request.POST['input_targets'], 
                input_penalties = request.POST['input_penalties'],
                input_relativecosts='[]', 
                name="Test", user=user)
        nplcc.save()
        t = nplcc.process_dict(nplcc.input_targets)
        p = nplcc.process_dict(nplcc.input_penalties)
        a = json.dumps([t,p])
        res = HttpResponse(a, 200)
        res['Content-Type'] = 'application/json'
        return res
    else:
        return HttpResponse('POST required', status=404)

def home(request):
    return render_to_response("nplcc/home.html")

def tutorial(request):
    return render_to_response("nplcc/tutorial.html")

def docs(request):
    return render_to_response("nplcc/docs.html")

def test(request):
    return render_to_response("seak/test.html")

def planning_units_geojson(request):
    def get_feature_json(geom_json, prop_json):
        return """{
            "type": "Feature",
            "geometry": %s, 
            "properties": %s
        }""" % (geom_json, prop_json)

    feature_jsons = []
    for pu in PlanningUnit.objects.all():
        fgj = get_feature_json(pu.geometry.json, json.dumps(
            {'name': pu.name, 
             'fid': pu.fid, 
             'area': pu.area}
        )) 
        feature_jsons.append(fgj)

    geojson = """{ 
      "type": "FeatureCollection",
      "features": [ %s ]
    }""" % (', \n'.join(feature_jsons),)

    return HttpResponse(geojson, content_type='application/json')

from django.views.decorators.cache import never_cache
# set headers to disable all client-side caching
@never_cache
def user_scenarios_geojson(request):
    from seak.models import Scenario

    # Why not use @login_required? 
    # That just redirects instead of giving proper Http Response code of 401
    user = request.user
    if user.is_anonymous() or not user.is_authenticated:
        return HttpResponse("You must be logged in to view your scenarios.", status=401)

    scenarios = Scenario.objects.filter(user=user).order_by('-date_modified')

    geojson = """{ 
      "type": "FeatureCollection",
      "features": [ %s ]
    }""" % (', \n'.join([s.geojson(None) for s in scenarios]),)

    return HttpResponse(geojson, content_type='application/json')
