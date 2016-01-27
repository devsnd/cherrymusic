from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User
from cherrymusic.apps.storage.models import File
from cherrymusic.apps.api.v1.serializers import FileSerializer
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE


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

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

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