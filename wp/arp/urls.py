from django.conf.urls.defaults import *
from arp.views import *

urlpatterns = patterns('',
    url(r'^test_params/$', test_params, name="arp-test_params"),
)

