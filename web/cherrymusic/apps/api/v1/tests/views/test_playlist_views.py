import os

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse
from django.db.models import Q

from cherrymusic.apps.core.models import User, Playlist
from cherrymusic.apps.api.v1.serializers import  PlaylistDetailSerializer, PlaylistListSerializer
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE

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

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

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



class TestExportPlaylistView(APITestCase):
    fixtures = ['directory', 'file', 'playlist', 'track', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('api:export-playlist')

    def test_unauthenticated_export_playlist_query(self):
        client = APIClient()
        response = client.get(self.url)

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

    def test_export_playlist_query(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(os.path.exists('/tmp/usr/src/app/music/admin.zip'))