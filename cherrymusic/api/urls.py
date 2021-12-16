from django.conf.urls import include
from django.urls import path
from rest_framework import routers, permissions

from youtube.views import YoutubeViewSet
from .views import FileViewSet, DirectoryViewSet, ServerStatusView, PlaylistViewSet, UserViewSet, \
    TrackViewSet, BrowseView, IndexDirectoryView, AlbumArtView, SearchView

router = routers.DefaultRouter()
router.register(r'file', FileViewSet)
router.register(r'directory', DirectoryViewSet)
router.register(r'playlist', PlaylistViewSet)
router.register(r'user', UserViewSet)
router.register(r'track', TrackViewSet)
router.register(r'youtube', YoutubeViewSet, basename='youtube')
router.register(r'search', SearchView, basename='search')

from rest_framework.schemas import get_schema_view

schema_view = get_schema_view(title="CherryMusic API")

urlpatterns = [
    path(r'schema/$', schema_view),
    path(r'status/$', ServerStatusView.as_view()),
    # path(r'stream/(?P<path>.*)', stream),
    # path(r'browse/(?P<path>.*)', BrowseView.as_view()),
    # path(r'index/(?P<path>.*)', IndexDirectoryView.as_view()),
    # path(r'albumart/(?P<path>.*)', AlbumArtView.as_view()),
    path(r'', include(router.urls)),
    path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
