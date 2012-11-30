import os
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def handle(self, *args, **options):
        from seak.views import planning_units_geojson
        from django.test.client import RequestFactory

        print "Caching the planning_units.geojson response..."
        request = RequestFactory().get('/seak/planning_units.geojson')
        planning_units_geojson(request)

