from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE


class TestBrowseView(APITestCase):
    fixtures = ['directory', 'file', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        path = 'Paisano'
        self.url = reverse('api:browse', args=[path])

    def test_unauthenticated_browse_query(self):
        client = APIClient()
        response = client.get(self.url)

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

    def test_browse_query(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = {
            "directories": [
                {
                    "parent": 11,
                    "path": "Revolucion",
                    "id": 12
                }
            ],
            "files": [],
            "current_path": "Paisano",
            "current": {
                "parent": 1,
                "path": "Paisano",
                "id": 11
            },
            "path": []
        }
        self.assertEqual(response.data, expected_data)


