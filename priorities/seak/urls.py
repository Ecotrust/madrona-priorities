from django.conf.urls import patterns, url
from seak.views import planning_units_geojson, field_lookup, \
        user_scenarios_geojson, shared_scenarios_geojson, id_lookup

urlpatterns = patterns('',
    url(r'^planning_units.geojson$', planning_units_geojson, name="seak-planning_units_geojson"),
    url(r'^field_lookup.json$', field_lookup, name="seak-field_lookup"),
    url(r'^id_lookup.json$', id_lookup, name="seak-id_lookup"),
    url(r'^scenarios.geojson$', user_scenarios_geojson, name="seak-user_scenarios_geojson"),
    url(r'^scenarios_shared.geojson$', shared_scenarios_geojson, name="seak-shared_scenarios_geojson"),
)

