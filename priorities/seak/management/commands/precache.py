import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from seak.models import Cost, ConservationFeature, Scenario

class Command(BaseCommand):

    def handle(self, *args, **options):
        from seak.views import planning_units_geojson
        from django.test.client import RequestFactory
        from madrona.layer_manager.views import get_json 

        print "Caching the planning_units.geojson response..."
        request = RequestFactory().get('/seak/planning_units.geojson')
        planning_units_geojson(request)

        print "Caching the layer_manager response..."
        request = RequestFactory().get('/layer_manager/layers.json')
        get_json(request)

        print "Caching scenario results..."
        for scenario in Scenario.objects.all():
            a = scenario.results

        print "Caching some tiles..."
        sz = settings.JS_OPTS['start_zoom']
        nz = settings.JS_OPTS['num_levels']

        zooms = [str(x) for x in range(sz,sz+nz)]

        ex = [str(x) for x in settings.JS_OPTS['extent']]
        extent = ' '.join([ex[1], ex[0], ex[3], ex[2]])

        layers = [ 
            ('utfgrid', 'json'),
            ('planning_units', 'png'),
        ]

        tilecfg = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..','..','tile_config','tiles.cfg'))
        for layer in layers:
            cmd = "tilestache-seed.py -c %s -l %s -e %s -b %s %s" % (tilecfg, layer[0], layer[1], extent, ' '.join(zooms[:-2]))
            print cmd
            os.popen(cmd)

        layers.extend([(x.dbf_fieldname, 'png') for x in Cost.objects.all()])
        layers.extend([(x.dbf_fieldname, 'png') for x in ConservationFeature.objects.all()])

        for z in zooms[:2]: # cache first two zoom levels only
            for layer in layers:
                cmd = "tilestache-seed.py -c %s -l %s -e %s -b %s %s" % (tilecfg, layer[0], layer[1], extent, z)
                print cmd
                os.popen(cmd)
