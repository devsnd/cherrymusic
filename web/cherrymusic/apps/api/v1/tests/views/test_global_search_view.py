from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse
from django.db.models import Q

from cherrymusic.apps.core.models import User
from cherrymusic.apps.storage.models import Directory, File
from cherrymusic.apps.api.v1.serializers import DirectorySerializer, FileSerializer
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE


class TestGlobalSearchList(APITestCase):
    fixtures = ['directory', 'file', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.search_param = 'paisano'
        self.url = reverse('api:search') + '?q=' + self.search_param

    def test_unauthenticated_search_query(self):
        client = APIClient()
        response = client.get(self.url)

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

    def test_search_query(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        query = self.search_param 

        max_directories = 10
        max_files = 50

        directories = Directory.objects.filter(path__icontains=query)[: max_directories]
        files = File.objects.filter(Q(filename__icontains=query) |
            Q(meta_title__icontains=query) | Q(meta_artist__icontains=query))[: max_files]

        dir_serializer = DirectorySerializer()
        file_serializer = FileSerializer()

        search_result_json = {
            'directories': [dir_serializer.to_representation(directory) for directory in directories],
            'files': [file_serializer.to_representation(file) for file in files],
        }

        self.assertEqual(response.data, search_result_json)
