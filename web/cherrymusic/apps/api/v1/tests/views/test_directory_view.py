from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User
from cherrymusic.apps.storage.models import Directory
from cherrymusic.apps.api.v1.serializers import DirectorySerializer
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE


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

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

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
