import coreapi
from rest_framework.decorators import action
from rest_framework.filters import BaseFilterBackend
from rest_framework.viewsets import GenericViewSet

from youtube.search import youtube_search


class YoutubeFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='query',
            location='query',
            required=True,
            type='string'
        )]


class YoutubeViewSet(GenericViewSet):
    filter_backends = (YoutubeFilterBackend,)

    @action(methods=['get'], detail=False)
    def search(self, request, query):
        return youtube_search(query)

