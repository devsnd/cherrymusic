import functools
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.generator.schemas import action_kwargs, ActionKwarg
from youtube.search import youtube_search


@functools.lru_cache(maxsize=256)
def cached_youtube_search(query):
    return youtube_search(query)


class YoutubeViewSet(GenericViewSet):
    @action(methods=['GET'], detail=False)
    @action_kwargs(ActionKwarg(name='query', type=str))
    def search(self, request, *args, **kwargs):
        query = request._request.GET['query']
        results = [result.asdict() for result in cached_youtube_search(query)]
        return Response(results)

