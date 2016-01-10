from django.test import TestCase
from django.contrib.auth.forms import AuthenticationForm

from cherrymusic.apps.core.models import User

class TestLoginView(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary')

    def test_auth_form(self):
        auth_data = {'username': 'temporary', 'password': 'temporary'}
        form = AuthenticationForm(data=auth_data)
        self.assertTrue(form.is_valid())

