from django.test import TestCase
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User, UserSettings, HotkeysSettings, MiscSettings

class TestLoginView(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@temporary.com', 'temporary')

    def test_call_view_loads(self):
        self.client.login(username='temporary', password='temporary')
        response = self.client.get(reverse('login-view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client/login.html')

    def test_login_view_fails_blank(self):
        response = self.client.post(reverse('login-view'), {})
        self.assertRedirects(response, reverse('login-view'))

    def test_login_view_fails_invalid(self):
        auth_data = {'username': 'temporary', 'password': 'bad_password'}
        response = self.client.post(reverse('login-view'), auth_data)
        self.assertRedirects(response, reverse('login-view'))

    def test_login_view_fails_invalid(self):
        auth_data = {'username': 'temporary', 'password': 'temporary'}
        response = self.client.post(reverse('login-view'), auth_data)
        self.assertRedirects(response, reverse('main-view'))

    def test_auth_form(self):
        auth_data = {'username': 'temporary', 'password': 'temporary'}
        form = AuthenticationForm(data=auth_data)
        self.assertTrue(form.is_valid())

class TestMainView(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@temporary.com', 'temporary')

    def test_call_view_denies_anonymous(self):
        response = self.client.get(reverse('main-view'), follow=True)
        self.assertRedirects(response, reverse('login-view'))
        response = self.client.post(reverse('main-view'), follow=True)
        self.assertRedirects(response, reverse('login-view'))

    def test_call_view_loads(self):
        self.client.login(username='temporary', password='temporary')
        response = self.client.get(reverse('main-view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client/main.html')

class TestUserSettings(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('temporary', 'temporary@temporary.com', 'temporary')
        self.user_settings = self.user.usersettings

    def test_user_settings_creationg(self):
        self.assertEqual(len(UserSettings.objects.filter(user=self.user)), 1)
        self.assertEqual(len(HotkeysSettings.objects.filter(user_settings=self.user_settings)), 1)
        self.assertEqual(len(MiscSettings.objects.filter(user_settings=self.user_settings)), 1)

    def test_user_settings_at_remove(self):
        self.user.delete()

        self.assertEqual(len(UserSettings.objects.filter(user=self.user)), 0)
        self.assertEqual(len(HotkeysSettings.objects.filter(user_settings=self.user_settings)), 0)
        self.assertEqual(len(MiscSettings.objects.filter(user_settings=self.user_settings)), 0)