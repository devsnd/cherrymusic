from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE


class TestAlbumArtView(APITestCase):
    fixtures = ['directory', 'file', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        path = 'Paisano'
        self.url = reverse('api:album-art', args=[path])

    def test_unauthenticated_album_art_query(self):
        client = APIClient()
        response = client.get(self.url)

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

    def test_album_art_query(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

