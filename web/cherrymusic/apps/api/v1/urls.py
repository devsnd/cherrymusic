from django.core.urlresolvers import reverse
from django.conf.urls import url, include

from rest_framework import routers

from .views import FileViewSet, DirectoryViewSet, ServerStatusView, PlaylistViewSet, \
    ImportPlaylistViewSet, ExportPlaylistViewSet, UserViewSet, UserSettingsViewSet,  \
    TrackViewSet, stream, BrowseView, IndexDirectoryView, AlbumArtView, GlobalSearchList

router = routers.DefaultRouter()
router.register(r'file', FileViewSet)
router.register(r'directory', DirectoryViewSet)
router.register(r'playlist', PlaylistViewSet)
router.register(r'user', UserViewSet)
router.register(r'user-settings', UserSettingsViewSet)
router.register(r'track', TrackViewSet)

urlpatterns = [
    url(r'status/$', ServerStatusView.as_view(), name="status"),
    url(r'stream/(?P<path>.*)', stream, name="stream"),
    url(r'browse/(?P<path>.*)', BrowseView.as_view(), name="browse"),
    url(r'^search/$', GlobalSearchList.as_view(), name="search"),
    url(r'^playlist/import/(?P<filename>.*)', ImportPlaylistViewSet.as_view(), name="import-playlist"),
    url(r'^playlist/export/$', ExportPlaylistViewSet.as_view(), name="export-playlist"),
    url(r'index/(?P<path>.*)', IndexDirectoryView.as_view(), name="index-files"),
    url(r'albumart/(?P<path>.*)', AlbumArtView.as_view(), name="album-art"),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='api-auth')),
    url(r'^rest-auth/', include('rest_auth.urls', namespace='rest-auth'))
]
