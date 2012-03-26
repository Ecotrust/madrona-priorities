from django.conf.urls.defaults import *
from seak.views import *

urlpatterns = patterns('',
    url(r'^test_params/$', test_params, name="seak-test_params"),
)

