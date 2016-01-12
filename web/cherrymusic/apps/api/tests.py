import json

from django.core.urlresolvers import reverse
from django.db.models import Q

from cherrymusic.apps.core.models import Playlist, Track, User, UserSettings
from cherrymusic.apps.storage.models import File, Directory
from cherrymusic.apps.api.serializers import FileSerializer, DirectorySerializer, UserSerializer, \
    CreateUserSerializer, UserSettingsSerializer, PlaylistDetailSerializer, \
    PlaylistListSerializer, TrackSerializer


from rest_framework import status
from rest_framework.test import APITestCase, APIClient

class TestFileView(APITestCase):
    fixtures = ['directory', 'file', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.serializer = FileSerializer()

    def test_file_query(self):
        url = reverse('api:file-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        files = File.objects.all()
        files_json = [self.serializer.to_representation(file_) for file_ in files] 
        self.assertEqual(response.data, files_json)

    def test_file_detailed(self):
        pk = 1
        url = reverse('api:file-detail', args=[pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        file_ = File.objects.get(pk=pk)
        file_json = self.serializer.to_representation(file_)

        self.assertEqual(response.data, file_json)

class TestDirectoryView(APITestCase):
    fixtures = ['directory', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.serializer = DirectorySerializer()

    def test_directory_query(self):
        url = reverse('api:directory-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        directories = Directory.objects.all()
        directories_json = [self.serializer.to_representation(directory) for directory in directories] 
        self.assertEqual(response.data, directories_json)

    def test_directory_detailed(self):
        pk = 1
        url = reverse('api:directory-detail', args=[pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        directory = Directory.objects.get(pk=pk)
        directory_json = self.serializer.to_representation(directory)

        self.assertEqual(response.data, directory_json)


class TestPlaylistView(APITestCase):
    fixtures = ['directory', 'file', 'playlist', 'track', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.list_serializer = PlaylistListSerializer()
        self.detail_serializer = PlaylistDetailSerializer()

    def test_playlist_query(self):
        url = reverse('api:playlist-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        playlists = Playlist.objects.filter(Q(owner=self.user) | Q(public=True))
        playlists_json = [self.list_serializer.to_representation(playlist) for playlist in playlists] 
        self.assertEqual(response.data, playlists_json)

    def test_playlist_detailed(self):
        pk = 1
        url = reverse('api:playlist-detail', args=[pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        playlist = Playlist.objects.get(pk=pk)
        playlist_json = self.detail_serializer.to_representation(playlist)

        self.assertEqual(response.data, playlist_json)

    def test_create_playlist(self):
        url = reverse('api:playlist-list')
        playlist_json = {"name": "TestPlaylist", "owner": 1, "public": False}

        response = self.client.post(url, playlist_json)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue( Playlist.objects.get(name=playlist_json['name']))

    def test_update_playlist(self):
        playlist_json = {
            "id": 2,
            "name": "Tipico pero Cierto",
            "owner": 1,
            "owner_name": "admin",
            "public": False,
            "created_at": "2016-01-11T18:13:40.002575Z",
            "loading": False,
            "tracks":[{
                    "playlist": 2,
                    "order": 6,
                    "type": 0,
                    "data": {
                        'id': 26}},
                {
                    "playlist": 2,
                    "order": 7,
                    "type":0,
                    "data":{
                        'id': 29}
                },
                {
                    "type": 0,
                    "data": {
                        'id': 45}},
                {
                "playlist":1,
                "order": 1,
                "type": 0,
                "data": {
                    'id': 44}}],
        }

        url = reverse('api:playlist-detail', args=[playlist_json['id']])

        response = self.client.put(url, playlist_json)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        playlist = Playlist.objects.get(pk=playlist_json['id'])
        tracks_number = len(playlist.track_set.all())
        self.assertEqual(tracks_number, len(playlist_json['tracks']))
