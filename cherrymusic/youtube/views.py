from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.generator.schemas import action_kwargs, ActionKwarg
from youtube.search import youtube_search


class YoutubeViewSet(GenericViewSet):
    @action(methods=['GET'], detail=False)
    @action_kwargs(ActionKwarg(name='query', type=str))
    def search(self, request, *args, **kwargs):
        query = request._request.GET['query']
        results = [result.asdict() for result in youtube_search(query)]
        return Response(results)

