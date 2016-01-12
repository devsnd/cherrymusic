import os
import time
import logging
import threading

from tinytag import TinyTag
from audiotranscode import audiotranscode

from sendfile import sendfile
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.db.models import Q
from django.conf import settings

from rest_framework import viewsets, filters, status
from rest_framework.exceptions import NotFound
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cherrymusic.apps.api.helper import ImageResponse, ImageRenderer
from cherrymusic.apps.core import pathprovider
from cherrymusic.apps.core.albumartfetcher import AlbumArtFetcher
from cherrymusic.apps.core.models import Playlist, Track, User, UserSettings
from cherrymusic.apps.core.pluginmanager import PluginManager
from cherrymusic.apps.storage.status import ServerStatus
from cherrymusic.apps.storage.models import File, Directory

from .permissions import IsOwnerOrReadOnly, IsOwnUser, IsAccountAdminOrReadOnly
from .serializers import FileSerializer, DirectorySerializer, UserSerializer, \
    CreateUserSerializer, UserSettingsSerializer, PlaylistDetailSerializer, \
    PlaylistListSerializer, TrackSerializer


logger = logging.getLogger(__name__)


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


class FileViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('filename', 'meta_title', 'meta_artist', 'meta_genre')   


class DirectoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Directory.objects.all()
    serializer_class = DirectorySerializer


class PlaylistViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    permission_classes = (IsOwnerOrReadOnly, )
    queryset = Playlist.objects.all()
    serializer_class = PlaylistDetailSerializer

    serializer_action_classes = {
        'list': PlaylistListSerializer,
        'retrieve': PlaylistDetailSerializer,
    }

    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('search', None)

        playlists = Playlist.objects.filter(Q(owner=user) | Q(public=True))

        if(query):
            return playlists.filter(name__icontains=query)

        return playlists

    def update(self, request, *args, **kwargs):
        playlist = self.get_object()
        playlist.track_set.all().delete()
        tracks = request.data['tracks']

        tracks = self._set_playlist_values_to_tracks(playlist.id, tracks)

        tracks_serializer = [TrackSerializer(data=track) for track in tracks]

        for track_serializer in tracks_serializer:
            track_serializer.is_valid()
            track_serializer.save()

        return super(PlaylistViewSet, self).update(request, *args, **kwargs)

    def _set_playlist_values_to_tracks(self, playlist_id, tracks):
        for index, track in enumerate(tracks):
            track['playlist'] = playlist_id
            track['order'] = index
            track['file'] = track['data']['id']

        return tracks

class ImportPlaylistViewSet(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        playlist_name = os.path.splitext(filename)[0]
        playlist_file_obj = request.data['file']

        tracks_file = self._get_track_files(playlist_file_obj)

        if any(track_file is None for track_file in tracks_file):
            return HttpResponse('Not all tracks where found', status=406)

        if Playlist.objects.filter(name=playlist_name).exists():
            return HttpResponse('Playlist with that name already exists', status=406)

        playlist = Playlist.objects.create(name=playlist_name, owner=self.request.user)
        playlist.tracks = [Track.objects.create(playlist=playlist, order=track_number, file=track_file)
            for track_number, track_file in enumerate(tracks_file)]
        playlist.save()

        playlist_serializer = PlaylistDetailSerializer()

        return Response(
            {'playlist': playlist_serializer.to_representation(playlist)})

    def _get_track_files(self, playlist_file_obj):
        tracks_path = self._get_tracks_path(playlist_file_obj)
        tracks_filename = [os.path.basename(track_path) for track_path in tracks_path]

        tracks_file = [self._find_track_file(track_filename) for track_filename in tracks_filename]

        return tracks_file

    def _get_tracks_path(self, playlist_file_obj):
        playlist_content = playlist_file_obj.read().decode('UTF-8')
        playlist_content = playlist_content.replace('\r', '')
        lines = playlist_content.split('\n')[4:-2]
        tracks_path = []
        for line in lines:
            if not line.startswith('#') and not line == '':
                tracks_path.append(line)

        return tracks_path

    def _find_track_file(self, track_filename):
        try:
            track_file = File.objects.filter(filename__icontains=track_filename)[0]
        except IndexError:
            track_file = None

        return track_file

class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAccountAdminOrReadOnly, )
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        return Response(content)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(id=self.request.user.id)

    def create(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Save password
        user, created = User.objects.get_or_create(username=serializer.data['username'])
        user.set_password(serializer.data['password'])
        user.is_staff = user.is_superuser = serializer.data['is_superuser']
        user.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class UserSettingsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsOwnUser, )
    queryset = UserSettings.objects.all()
    serializer_class = UserSettingsSerializer

    def get_queryset(self):
        user = self.request.user
        return UserSettings.objects.filter(user=user)

class TrackViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = Track.objects.all()
    serializer_class = TrackSerializer


class ServerStatusView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        return Response([ServerStatus.get_latest()])

def stream(request, path):
    basedir = Directory.get_basedir().absolute_path()
    file_path = str(basedir / path)
    mime_type = 'audio/ogg'

    if(file_path.lower().endswith(('mp3', 'ogg'))):
        return sendfile(
            request,
            file_path,
            attachment=False,
            mimetype=mime_type,     
        )

    file_path_without_ext = os.path.splitext(file_path)[0]
    new_file_path = '/tmp' + file_path_without_ext + '.ogg'

    if not os.path.isfile(new_file_path):
        transcode_thread = threading.Thread(target=audiotranscode.AudioTranscode().transcode,
            args=(file_path, new_file_path))
        transcode_thread.start()

        return StreamingHttpResponse(
            stream_audio(file_path),
            content_type=mime_type
        )

    return sendfile(
        request,
        new_file_path,
        root_url='/tmp' + settings.SENDFILE_URL,
        root_directory='/tmp' + settings.SENDFILE_ROOT,
        attachment=False,
        mimetype=mime_type,
    )

def stream_audio(audiofile):
    yield from audiotranscode.AudioTranscode().transcode_stream(audiofile, newformat='ogg')

class AlbumArtView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ImageRenderer, )

    def get(self, request, path):
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
        else:
            #fetch album art from online source
            try:
                foldername = os.path.basename(file_path)
                keywords = foldername
                logger.info("Fetching album art for keywords: %s" % keywords)
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


class BrowseView(APIView):
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

class GlobalSearchList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query = self.request.query_params.get('q', '')

        max_directories = 10
        max_files = 50
        
        directories = Directory.objects.filter(path__icontains=query)[: max_directories]
        files = File.objects.filter(Q(filename__icontains=query) |
            Q(meta_title__icontains=query) | Q(meta_artist__icontains=query))[: max_files]

        dir_serializer = DirectorySerializer()
        file_serializer = FileSerializer()

        return Response({
            'directories': [dir_serializer.to_representation(directory) for directory in directories],
            'files': [file_serializer.to_representation(file) for file in files],
        })


class MessageOfTheDayView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        message_of_the_day = 'Hello good sir.'
        Response(
            PluginManager.digest(PluginManager.Event.GET_MOTD, request.user, message_of_the_day)
        )