from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User, Track
from cherrymusic.apps.api.v1.serializers import  TrackSerializer
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE


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

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

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