from django.conf.urls import *
from seak.views import *

urlpatterns = patterns('',
    url(r'^test_params/$', test_params, name="seak-test_params"),
    url(r'^planning_units.geojson$', planning_units_geojson, name="seak-planning_units_geojson"),
    url(r'^field_lookup.json$', field_lookup, name="seak-field_lookup"),
    url(r'^scenarios.geojson$', user_scenarios_geojson, name="seak-user_scenarios_geojson"),
    url(r'^scenarios_shared.geojson$', shared_scenarios_geojson, name="seak-shared_scenarios_geojson"),
    url(r'^test$', test, name="test"),
)

