from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User, File
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE

class TestStatusView(APITestCase):
    fixtures = ['directory', 'file', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('api:status')

    def test_unauthenticated_status_query(self):
        client = APIClient()
        response = client.get(self.url)

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

    def test_status_query(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        status_json = {
            'indexed_files': File.objects.count(),
            'meta_indexed_files': File.objects.filter(meta_index_date__isnull=False).count(),
            'active_users': 0
        }

        self.assertEqual(response.data[0], status_json)
