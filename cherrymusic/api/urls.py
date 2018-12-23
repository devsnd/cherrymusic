from django.conf.urls import url, include
from rest_framework import routers, permissions
from .views import FileViewSet, DirectoryViewSet, ServerStatusView, PlaylistViewSet, UserViewSet, \
    TrackViewSet, BrowseView, IndexDirectoryView, AlbumArtView

router = routers.DefaultRouter()
router.register(r'file', FileViewSet)
router.register(r'directory', DirectoryViewSet)
router.register(r'playlist', PlaylistViewSet)
router.register(r'user', UserViewSet)
router.register(r'track', TrackViewSet)

from rest_framework.schemas import get_schema_view

schema_view = get_schema_view(title="CherryMusic API")

urlpatterns = [
    url(r'schema/$', schema_view),
    url(r'status/$', ServerStatusView.as_view()),
    # url(r'stream/(?P<path>.*)', stream),
    # url(r'browse/(?P<path>.*)', BrowseView.as_view()),
    # url(r'index/(?P<path>.*)', IndexDirectoryView.as_view()),
    # url(r'albumart/(?P<path>.*)', AlbumArtView.as_view()),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
