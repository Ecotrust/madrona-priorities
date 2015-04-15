from django.conf.urls import *
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns(
    'seak.views',
    url(r'^$', 'home'),
    url(r'^map', 'map', name='map'),
    url(r'^news/description', 'description', name="description"),
    url(r'^tiles/', 'tiles', name="tiles"),
)

urlpatterns += patterns(
    '',
    (r'^seak/', include('seak.urls')),
    (r'^analysistools/', include('madrona.analysistools.urls')),
)

urlpatterns += patterns(
    'madrona',
    (r'^accounts/', include('madrona.openid.urls')),
    (r'^accounts/profile/', include('madrona.user_profile.urls')),
    (r'^faq/', include('madrona.simplefaq.urls')),
    (r'^features/', include('madrona.features.urls')),
    (r'^help/', include('madrona.help.urls')),
    (r'^kml/', include('madrona.kmlapp.urls')),
    (r'^layers/', include('madrona.layers.urls')),
    (r'^layer_manager/', include('madrona.layer_manager.urls')),
    (r'^loadshp/', include('madrona.loadshp.urls')),
    (r'^manipulators/', include('madrona.manipulators.urls')),
    (r'^news/', include('madrona.news.urls')),
    (r'^screencasts/', include('madrona.screencasts.urls')),
    (r'^staticmap/', include('madrona.staticmap.urls')),
    (r'^studyregion/', include('madrona.studyregion.urls')),
    (r'^bookmark/', include('madrona.bookmarks.urls')),
)

urlpatterns += patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
)

# Useful for serving files when using the django dev server
urlpatterns += patterns(
    '',
    (r'^media(.*)/upload/', 'madrona.common.views.forbidden'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
        'show_indexes': True
    }),
)
