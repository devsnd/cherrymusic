import time

import logging
import operator
import os
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import StreamingHttpResponse, Http404
from django.utils.translation import ugettext_lazy as _
from django_filters import FilterSet, BooleanFilter
from functools import reduce
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from api.generator.schemas import action_kwargs, ActionKwarg
from api.helper import ImageResponse, ImageRenderer
from core import pathprovider
from core.albumartfetcher import AlbumArtFetcher
from core.config import Config
from core.pluginmanager import PluginManager
from ext.audiotranscode import AudioTranscode
from ext.tinytag import TinyTag
from playlist.models import Track, Playlist
from storage.models import File, Directory, Artist, Album
from storage.status import ServerStatus
from .serializers import FileSerializer, DirectorySerializer, UserSerializer, \
    TrackSerializer, PlaylistSerializer, ArtistSerializer, AlbumSerializer, \
    SimpleDirectorySerializer

logger = logging.getLogger(__name__)

User = get_user_model()

DEBUG_SLOW_SERVER = False

class SlowServerMixin(object):
    def dispatch(self, *args, **kwargs):
        if DEBUG_SLOW_SERVER:
            time.sleep(1)
        return super().dispatch(*args, **kwargs)


# http://stackoverflow.com/a/22922156/1191373
class MultiSerializerViewSetMixin(object):
    def get_serializer_class(self):
        """
        Look for serializer class in self.serializer_action_classes, which
        should be a dict mapping action name (key) to serializer class (value),
        i.e.:

        class MyViewSet(MultiSerializerViewSetMixin, ViewSet):
            serializer_class = MyDefaultSerializer
            serializer_action_classes = {
               'list': MyListSerializer,
               'my_action': MyActionSerializer,
            }

            @action
            def my_action:
                ...

        If there's no entry for that action then just fallback to the regular
        get_serializer_class lookup: self.serializer_class, DefaultSerializer.

        Thanks gonz: http://stackoverflow.com/a/22922156/11440

        """
        try:
            return self.__class__.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super(MultiSerializerViewSetMixin, self).get_serializer_class()


class FileViewSet(SlowServerMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = File.objects.all()
    serializer_class = FileSerializer

    @action(detail=True, methods=['get'])
    def transcode(self, request, pk=None):
        def transcode_stream(audiofile, format, start_time):
            yield from AudioTranscode().transcode_stream(
                audiofile, newformat=format, starttime=int(start_time)
            )
        file = self.get_object()
        return StreamingHttpResponse(
            transcode_stream(str(file.absolute_path()), 'ogg', 0),
            content_type='application/octet-stream'
        )

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        def file_iterator(filepath, chunk_size=512):
            with open(filepath, 'rb') as fh:
                while True:
                    data = fh.read(chunk_size)
                    if data:
                        yield data
                    else:
                        break

        file = self.get_object()
        return StreamingHttpResponse(
            file_iterator(file.absolute_path(), 8192),
            content_type='application/octet-stream'
        )


class DirectoryFilter(FilterSet):
    ''' filter on snapshot fields '''
    basedir = BooleanFilter(field_name='parent', lookup_expr='isnull')

    class Meta:
        model = Directory
        fields = ('basedir', )


class DirectoryViewSet(SlowServerMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Directory.objects.all()
    serializer_class = DirectorySerializer
    filter_class = DirectoryFilter

    @action(methods=['get'], detail=False)
    def basedirs(self, request, *args, **kwargs):
        base_dirs = Directory.objects.filter(parent__isnull=True)
        serializer = SimpleDirectorySerializer()
        sub_directories = [
            serializer.to_representation(base_dir) for base_dir in base_dirs
        ]
        data = {
            'id': -1,
            'parent': None,
            'path': 'Root',
            'sub_directories': sub_directories,
            'files': []
        }
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PlaylistViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer

    def get_serializer(self, *args, **kwargs):
        kwargs['data']['owner'] = UserSerializer().to_representation(self.request.user)
        serializer = super().get_serializer(*args, **kwargs)
        return serializer


class UserViewSet(SlowServerMixin, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = User.objects.all()
    serializer_class = UserSerializer


class TrackViewSet(SlowServerMixin, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = Track.objects.all()
    serializer_class = TrackSerializer


class ServerStatusView(SlowServerMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        return Response([ServerStatus.get_latest()])


class AlbumArtView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ImageRenderer, )

    def get(self, request, path):
        config = Config.get_config()
        file_path = Directory.get_basedir().absolute_path() / path
        if not file_path.exists():
            raise NotFound()

        # try fetching from the audio file
        if file_path.is_file():
            tag = TinyTag.get(str(file_path), image=True)
            image_data = tag.get_image()
            if image_data:
                return ImageResponse(image_data=image_data)
            # try the parent directory of the file
            file_path = file_path / '..'

        #try getting a cached album art image
        file_cache_path = pathprovider.albumArtFilePath(str(file_path))
        if os.path.exists(file_cache_path):
            with open(file_cache_path, 'rb') as fh:
                return ImageResponse(image_data=fh.read())

        #try getting album art inside local folder
        fetcher = AlbumArtFetcher()
        header, data, resized = fetcher.fetchLocal(str(file_path))

        if header:
            if resized:
                #cache resized image for next time
                with open(file_cache_path, 'wb') as fh:
                    fh.write(data)
            return ImageResponse(image_data=data)
        elif config.get('media.fetch_album_art', False):
            #fetch album art from online source
            try:
                foldername = os.path.basename(file_path)
                keywords = foldername
                logger.info(_("Fetching album art for keywords {keywords!r}").format(keywords=keywords))
                header, data = fetcher.fetch(keywords)
                if header:
                    with open(file_cache_path, 'wb') as fh:
                        fh.write(data)
                    return ImageResponse(image_data=data)
            except:
                pass
        raise Http404()


class IndexDirectoryView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, path):
        basedir = Directory.get_basedir()
        if path:
            path_elements = path.split('/')
            *parent_dirs, current_dir = basedir.get_sub_path_directories(path_elements)
            current_dir.reindex()
        else:
            basedir.reindex()
        return Response()


class BrowseView(SlowServerMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, path):
        basedir = Directory.get_basedir()
        if path:
            # check for subdirs
            path_elements = path.split('/')
            *parent_dirs, current_dir = basedir.get_sub_path_directories(path_elements)
        else:
            # list the basedir if no path was given
            parent_dirs, current_dir = [], basedir
        files, directories = current_dir.listdir()
        dir_serializer = DirectorySerializer()
        file_serializer = FileSerializer()
        current_dir_path = str(current_dir.relative_path())
        return Response({
            'current': dir_serializer.to_representation(current_dir),
            'current_path': current_dir_path,
            'path': [dir_serializer.to_representation(directory) for directory in parent_dirs],
            'files': [file_serializer.to_representation(file) for file in files],
            'directories': [dir_serializer.to_representation(directory) for directory in directories],
        })

class MessageOfTheDayView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        message_of_the_day = 'Hello good sir.'
        Response(
            PluginManager.digest(PluginManager.Event.GET_MOTD, request.user, message_of_the_day)
        )


class SearchView(SlowServerMixin, GenericViewSet):
    ARTIST_LIMIT = 6
    ALBUM_LIMIT = 6
    SONG_LIMIT = 8

    @classmethod
    def make_word_filter(cls, words, prefix):
        filters = ({f'{prefix}__icontains': word} for word in words)
        qs = (Q(**filter) for filter in filters)
        return reduce(operator.or_, qs)

    @action(methods=['get'], detail=False)
    @action_kwargs(ActionKwarg('query'))
    def search(self, request):
        query = request._request.GET['query']
        words = query.strip().split()
        if not words:
            return Response({
                'artists': [],
                'albums': [],
                'files': [],
            })

        artists = list(
            Artist.objects
            .filter(SearchView.make_word_filter(words, 'name'))
            .order_by('name')
            [:SearchView.ARTIST_LIMIT]
        )

        album_filters = [Q(SearchView.make_word_filter(words, 'name'))]
        if artists:
            # find all albums made by the artist that was found in addition to
            # the albums that have the proper name
            album_filters.append(
                reduce(operator.or_, (Q(albumartist=artist) for artist in artists))
            )
        albums = (
            Album.objects
            .filter(reduce(operator.or_, album_filters))
            .order_by('name')
            [:SearchView.ALBUM_LIMIT]
        )

        file_filters = [SearchView.make_word_filter(words, 'meta_data__title')]
        # find tracks made by this artist, if any
        if artists:
            file_filters.append(
                reduce(operator.or_, (Q(meta_data__artist=artist) for artist in artists))
            )
        files = (
            File.objects
            .filter(reduce(operator.or_, file_filters))
            .order_by('meta_data__album', 'meta_data__track')
            [:SearchView.SONG_LIMIT]
        )
        return Response({
            'artists': [ArtistSerializer().to_representation(i) for i in artists],
            'albums': [AlbumSerializer().to_representation(i) for i in albums],
            'files': [FileSerializer().to_representation(i) for i in files],
        })
