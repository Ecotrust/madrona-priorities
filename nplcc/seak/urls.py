from django.conf.urls.defaults import *
from seak.views import *
from django.views.decorators.cache import cache_page

urlpatterns = patterns('',
    url(r'^test_params/$', test_params, name="seak-test_params"),
    url(r'^planning_units.geojson$', cache_page(3600)(planning_units_geojson), name="seak-planning_units_geojson"),
    url(r'^scenarios.geojson$', user_scenarios_geojson, name="seak-user_scenarios_geojson"),
    url(r'^scenarios_shared.geojson$', shared_scenarios_geojson, name="seak-shared_scenarios_geojson"),
    url(r'^test$', test, name="test"),
)

