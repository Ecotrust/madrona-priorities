from django.conf.urls.defaults import *
from arp.views import *

urlpatterns = patterns('',
    url(r'^$', home, name="arp-home"),
)

