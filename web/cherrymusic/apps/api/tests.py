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

unauthenticated_response = {'detail': 'Authentication credentials were not provided.'}

class TestFileView(APITestCase):
    fixtures = ['directory', 'file', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.serializer = FileSerializer()

    def test_unauthenticated_file_query(self):
        url = reverse('api:file-list')
        client = APIClient()
        response = client.get(url)

        self.assertEqual(response.data, unauthenticated_response)

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

    def test_unauthenticated_directory_query(self):
        url = reverse('api:directory-list')
        client = APIClient()
        response = client.get(url)

        self.assertEqual(response.data, unauthenticated_response)

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

    def test_unauthenticated_playlist_query(self):
        url = reverse('api:playlist-list')
        client = APIClient()
        response = client.get(url)

        self.assertEqual(response.data, unauthenticated_response)

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
        playlist_json = {
            "name": "TestPlaylist",
            "tracks":[
                {
                    "type": 0,
                    "data":{
                        "id":49
                    }
                }
            ],
            "public": False
        }

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


class TestUserViewSet(APITestCase):
    fixtures = ['user']

    def setUp(self):
        self.user = User.objects.get(is_superuser=False)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.superuser = User.objects.get(is_superuser=True)
        self.superuser_client = APIClient(enforce_csrf_checks=True)
        self.superuser_client.force_authenticate(user=self.superuser)
        self.serializer = UserSerializer()
        self.user_json = {
            "username": "test",
            "password": "test",
            "is_superuser": False,
            "email": "test@test.com",
        }

    def test_anonymous_query(self):
        url = reverse('api:user-list')
        client = APIClient()
        response = client.get(url)

        self.assertEqual(response.data, unauthenticated_response)

    def test_user_query(self):
        url = reverse('api:user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_json = self.serializer.to_representation(self.user)
        self.assertEqual(response.data[0], user_json)

    def test_superuser_query(self):
        url = reverse('api:user-list')
        response = self.superuser_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users = User.objects.all()

        users_json = [self.serializer.to_representation(user) for user in users] 

        self.assertEqual(response.data, users_json)

    def test_user_create(self):
        url = reverse('api:user-list')

        response = self.client.post(url, self.user_json)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_superuser_create(self):
        url = reverse('api:user-list')

        response = self.superuser_client.post(url, self.user_json)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data['username'], self.user_json['username'])


class TestUserSettingsView(APITestCase):
    fixtures = ['user', 'user_settings', 'hotkeys_settings', 'misc_settings']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.serializer = UserSettingsSerializer()

    def test_unauthenticated_user_settings_query(self):
        url = reverse('api:usersettings-list')
        client = APIClient()
        response = client.get(url)

        self.assertEqual(response.data, unauthenticated_response)

    def test_user_settings_query(self):
        url = reverse('api:usersettings-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_settings = self.user.usersettings
        user_settings_json = self.serializer.to_representation(user_settings) 
        self.assertEqual(response.data[0], user_settings_json)

    def test_another_usersettings_query(self):
        pk = 2
        url = reverse('api:usersettings-detail', args=[pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class TestTrackView(APITestCase):
    fixtures = ['directory', 'file', 'playlist', 'track', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.serializer = TrackSerializer()

    def test_unauthenticated_track_query(self):
        url = reverse('api:track-list')
        client = APIClient()
        response = client.get(url)

        self.assertEqual(response.data, unauthenticated_response)

    def test_track_query(self):
        url = reverse('api:track-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tracks = Track.objects.all()
        tracks_json = [self.serializer.to_representation(track) for track in tracks] 
        self.assertEqual(response.data, tracks_json)

    def test_track_detailed(self):
        pk = 1
        url = reverse('api:track-detail', args=[pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        track = Track.objects.get(pk=pk)
        track_json = self.serializer.to_representation(track)

        self.assertEqual(response.data, track_json)

class TestStatusView(APITestCase):
    fixtures = ['directory', 'file', 'playlist', 'track', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.serializer = TrackSerializer()
        self.url = reverse('api:status')

    def test_unauthenticated_status_query(self):
        client = APIClient()
        response = client.get(self.url)

        self.assertEqual(response.data, unauthenticated_response)

    def test_status_query(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        status_json = {
            'indexed_files': File.objects.count(),
            'meta_indexed_files': File.objects.filter(meta_index_date__isnull=False).count(),
            'active_users': 0
        }

        self.assertEqual(response.data[0], status_json)
