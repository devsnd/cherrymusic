import os
import time
import logging
import threading
import zipfile

from tinytag import TinyTag
from audiotranscode import audiotranscode

from sendfile import sendfile
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse

from rest_framework import viewsets, filters, status
from rest_framework.exceptions import NotFound
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cherrymusic.apps.api.v1.helper import ImageResponse, ImageRenderer
from cherrymusic.apps.core import pathprovider
from cherrymusic.apps.core.albumartfetcher import AlbumArtFetcher
from cherrymusic.apps.core.models import Playlist, Track, User, UserSettings
from cherrymusic.apps.core.pluginmanager import PluginManager
from cherrymusic.apps.storage.status import ServerStatus
from cherrymusic.apps.storage.models import File, Directory

from cherrymusic.apps.api.v1.permissions import IsOwnerOrReadOnly, IsOwnUser, IsAccountAdminOrReadOnly
from cherrymusic.apps.api.v1.serializers import (
    FileSerializer, DirectorySerializer, UserSerializer, CreateUserSerializer, UserSettingsSerializer,
    PlaylistDetailSerializer, PlaylistListSerializer, TrackSerializer
    )
    


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
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('filename', 'meta_title', 'meta_artist', 'meta_genre')   


class DirectoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Directory.objects.all()
    serializer_class = DirectorySerializer


class PlaylistViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    permission_classes = (IsOwnerOrReadOnly, IsAuthenticated)
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

    def create(self, request, *args, **kwargs):
        playlist_json = request.data
        playlist_json['owner'] = request.user.id

        if Playlist.objects.filter(name=playlist_json['name'], owner=request.user).count() > 0:
            return Response({'detail': ['Already exits a playlist with that name and user.']},
                    status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=playlist_json)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        playlist = Playlist.objects.get(name=playlist_json['name'], owner=request.user)
        
        if not 'tracks' in request.data:
            return Response({'tracks': ['This field is required.']},
                     status=status.HTTP_400_BAD_REQUEST)
        
        tracks = request.data['tracks']
            
        tracks = self._set_playlist_values_to_tracks(playlist.id, tracks)
        self._save_tracks(tracks)
        
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        if 'tracks' in request.data:
            playlist = self.get_object()
            playlist.track_set.all().delete()
    
            tracks = request.data['tracks']
            tracks = self._set_playlist_values_to_tracks(playlist.id, tracks)
            self._save_tracks(tracks)

        return super(PlaylistViewSet, self).update(request, *args, **kwargs)

    def _set_playlist_values_to_tracks(self, playlist_id, tracks):
        for index, track in enumerate(tracks):
            track['playlist'] = playlist_id
            track['order'] = index
            track['file'] = track['data']['id']

        return tracks

    def _save_tracks(self, tracks):
        tracks_serializer = [TrackSerializer(data=track) for track in tracks]

        for track_serializer in tracks_serializer:
            track_serializer.is_valid()
            track_serializer.save()

        return True

class ImportPlaylistViewSet(APIView):
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        playlist_name = os.path.splitext(filename)[0]
        playlist_file_obj = request.data['file']

        tracks_file = self._get_track_files(playlist_file_obj)

        if any(track_file is None for track_file in tracks_file):
            return Response(
                {'detail': 'Not all tracks where found'},
                status=status.HTTP_400_BAD_REQUEST
                )

        if Playlist.objects.filter(name=playlist_name).exists():
            return Response(
                {'detail': 'Playlist with that name already exists'},
                status=status.HTTP_400_BAD_REQUEST
                )

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

class ExportPlaylistViewSet(APIView):
    def get(self, request, format=None):
        base_url = request.build_absolute_uri().replace(reverse('api:export-playlist'), "")

        playlists = Playlist.objects.filter(owner=request.user)
        playlists_zip_directory = '/tmp' + settings.SENDFILE_ROOT
        playlists_zip_path = os.path.join(playlists_zip_directory, request.user.username + '.zip')

        if not os.path.exists(playlists_zip_directory):
            os.makedirs(playlists_zip_directory)

        with zipfile.ZipFile(playlists_zip_path, 'w') as playlists_zip:
            for playlist in playlists:
                tracks = playlist.track_set.all()
                tracks_url = [
                    base_url + reverse('api:stream', args=['']) + str(track.file.relative_path())
                    for track in tracks
                    ]
                playlist_string = '\n'.join(tracks_url)
                playlists_zip.writestr(playlist.name + '.m3u' , playlist_string)

        return sendfile(
            request,
            playlists_zip_path,
            root_url='/tmp' + settings.SENDFILE_URL,
            root_directory='/tmp' + settings.SENDFILE_ROOT,
            attachment=True,
            attachment_filename='playlists.zip',
            mimetype='application/x-zip-compressed',
        )

class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAccountAdminOrReadOnly, IsAuthenticated)
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
    permission_classes = (IsOwnUser, IsAuthenticated)
    queryset = UserSettings.objects.all()
    serializer_class = UserSettingsSerializer

    def create(self, request):
        raise Http404()

    def get_queryset(self):
        user = self.request.user
        return UserSettings.objects.filter(user=user)

class TrackViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer

class ServerStatusView(APIView):
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
    def get(self, request, path):
        if cache.get('is_block_indexing'):
            raise Http404()
        cache.set('is_block_indexing', True)
        try:
            basedir = Directory.get_basedir()
            if path:
                path_elements = path.split('/')
                *parent_dirs, current_dir = basedir.get_sub_path_directories(path_elements)
                current_dir.reindex()
            else:
                basedir.reindex()
        except:
            raise
        finally:
            cache.set('is_block_indexing', False)

        cache.set('is_block_indexing', False)

        return Response()


class BrowseView(APIView):
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
    def get(self, request):
        message_of_the_day = 'Hello good sir.'
        Response(
            PluginManager.digest(PluginManager.Event.GET_MOTD, request.user, message_of_the_day)
        )