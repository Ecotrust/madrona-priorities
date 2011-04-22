from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    (r'^arp/', include('arp.urls')),
)

urlpatterns += patterns('',
    # Include all lingcod app urls. 
    (r'', include('lingcod.common.urls')),
)
