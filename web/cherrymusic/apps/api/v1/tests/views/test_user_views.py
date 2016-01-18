from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User
from cherrymusic.apps.api.v1.serializers import  UserSerializer, UserSettingsSerializer
from cherrymusic.apps.api.v1.tests.views import UNAUTHENTICATED_RESPONSE

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

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

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
    fixtures = ['user_settings', 'hotkeys_settings', 'misc_settings', 'user']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_authenticate(user=self.user)
        self.serializer = UserSettingsSerializer()
        self.url = reverse('api:usersettings-list')
        self.user_settings_json = {
            "user": 1,
            "hotkeys": {
                "increase_volume": "ctrl+up",
                "decrease_volume": "ctrl+down",
                "toggle_mute": "ctrl+m",
                "previous_track": "ctrl+left",
                "next_track": "ctrl+right",
                "toggle_play": "space"
            },
            "misc": {
                "auto_play": False,
                "confirm_closing": True,
                "show_album_art": True,
                "remove_when_queue": True
            }
        }


    def test_unauthenticated_user_settings_query(self):
        client = APIClient()
        response = client.get(self.url)

        self.assertEqual(response.data, UNAUTHENTICATED_RESPONSE)

    def test_user_settings_query(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_settings = self.user.usersettings
        user_settings_json = self.serializer.to_representation(user_settings) 
        self.assertEqual(response.data[0], user_settings_json)

    def test_another_usersettings_query(self):
        pk = 2
        url = reverse('api:usersettings-detail', args=[pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_settings_create(self):
        response = self.client.post(self.url, self.user_settings_json)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_settings_update(self):
        pk = self.user.id
        url = reverse('api:usersettings-detail', args=[pk])
        response = self.client.put(url, self.user_settings_json)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data, self.user_settings_json)