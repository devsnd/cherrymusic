from django.test import TestCase
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse

from cherrymusic.apps.core.models import User

class TestLoginView(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@temporary.com', 'temporary')

    def test_call_view_loads(self):
        self.client.login(username='temporary', password='temporary')
        response = self.client.get(reverse('login_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client/login.html')

    def test_login_view_fails_blank(self):
        response = self.client.post(reverse('login_view'), {})
        self.assertRedirects(response, reverse('login_view'))

    def test_login_view_fails_invalid(self):
        auth_data = {'username': 'temporary', 'password': 'bad_password'}
        response = self.client.post(reverse('login_view'), auth_data)
        self.assertRedirects(response, reverse('login_view'))

    def test_login_view_fails_invalid(self):
        auth_data = {'username': 'temporary', 'password': 'temporary'}
        response = self.client.post(reverse('login_view'), auth_data)
        self.assertRedirects(response, reverse('main_view'))

    def test_auth_form(self):
        auth_data = {'username': 'temporary', 'password': 'temporary'}
        form = AuthenticationForm(data=auth_data)
        self.assertTrue(form.is_valid())

class TestMainView(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@temporary.com', 'temporary')

    def test_call_view_denies_anonymous(self):
        response = self.client.get(reverse('main_view'), follow=True)
        self.assertRedirects(response, reverse('login_view'))
        response = self.client.post(reverse('main_view'), follow=True)
        self.assertRedirects(response, reverse('login_view'))

    def test_call_view_loads(self):
        self.client.login(username='temporary', password='temporary')
        response = self.client.get(reverse('main_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client/main.html')