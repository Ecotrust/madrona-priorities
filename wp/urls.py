from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('lingcod.common.views',
    url(r'^tool/$', 'map', name='map'),
)

urlpatterns += patterns('',
    (r'^arp/', include('arp.urls')),
    (r'^analysistools/', include('lingcod.analysistools.urls')),
)

urlpatterns += patterns('arp.views',
    url(r'^$', 'home', name='home'),
    url(r'^tutorial.html$', 'tutorial', name='tutorial'),
    url(r'^docs.html$', 'docs', name='docs'),
)
urlpatterns += patterns('lingcod',
    (r'^accounts/', include('lingcod.openid.urls')),
    (r'^accounts/profile/', include('lingcod.user_profile.urls')),
    (r'^faq/', include('lingcod.simplefaq.urls')),
    (r'^features/', include('lingcod.features.urls')),
    (r'^help/', include('lingcod.help.urls')),
    (r'^kml/', include('lingcod.kmlapp.urls')),
    (r'^layers/', include('lingcod.layers.urls')),
    (r'^loadshp/', include('lingcod.loadshp.urls')),
    (r'^manipulators/', include('lingcod.manipulators.urls')),
    (r'^news/', include('lingcod.news.urls')),
    (r'^screencasts/', include('lingcod.screencasts.urls')),
    (r'^staticmap/', include('lingcod.staticmap.urls')),
    (r'^studyregion/', include('lingcod.studyregion.urls')),
    (r'^bookmark/', include('lingcod.bookmarks.urls')),
)

urlpatterns += patterns('',
    (r'^admin/', include(admin.site.urls)),
)

# Useful for serving files when using the django dev server
urlpatterns += patterns('',
    (r'^media(.*)/upload/', 'lingcod.common.views.forbidden'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True }),
)
