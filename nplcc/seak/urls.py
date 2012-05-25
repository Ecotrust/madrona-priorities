from django.conf.urls.defaults import *
from seak.views import *

urlpatterns = patterns('',
    url(r'^test_params/$', test_params, name="seak-test_params"),
    url(r'^planning_units.geojson$', planning_units_geojson, name="seak-planning_units_geojson"),
    url(r'^test$', test, name="test"),
)

