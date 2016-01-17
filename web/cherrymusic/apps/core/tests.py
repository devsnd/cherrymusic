import os

from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth.forms import AuthenticationForm

from cherrymusic.apps.core import album_art_fetcher
from cherrymusic.apps.core import pathprovider
from cherrymusic.apps.core.models import User

class TestUsernameCaseInsensitive(TestCase):

    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@temporary.com', 'temporary')
    
    def test_auth_form(self):
        auth_data = {'username': 'temporary', 'password': 'temporary'}
        form = AuthenticationForm(data=auth_data)
        self.assertTrue(form.is_valid())

    def test_username_case_insensitive(self):
        auth_data = {'username': 'Temporary', 'password': 'temporary'}
        form = AuthenticationForm(data=auth_data)
        self.assertTrue(form.is_valid())

    def test_invalid_user_name(self):
        with self.assertRaises(IntegrityError) as cm:
            user = User.objects.create_user('Temporary', 'temporary@temporary.com', 'temporary')

class TestPathprovider(TestCase):
    def test_album_art_file_path(self):
        album_art_path = pathprovider.album_art_file_path('/usr/src/app/music/foo')
        self.assertEqual('/tmp/albumart/18ba70bfc245f33a9b9c7447aa314899.thumb' , album_art_path)

class TestAlbumArtFetcher(TestCase):
    def test_resize(self):
        fetcher = album_art_fetcher.AlbumArtFetcher()
        test_path = '/usr/src/app/cherrymusic/apps/core/tests/resize'
        image_path = os.path.join(test_path, 'libreto.jpg')
        size = (80, 80)
        header, data = fetcher.resize( image_path, size)

        with open(os.path.join(test_path, 'libreto.thumb'), 'rb') as image_file:
            result_data = image_file.read()

        self.assertEqual(header, {'Content-Length': 2282, 'Content-Type': 'image/jpeg'})
        self.assertEqual(result_data, data)

    def test_fetch_local_with_resizing(self):
        fetcher = album_art_fetcher.AlbumArtFetcher()
        test_path = '/usr/src/app/cherrymusic/apps/core/tests/resize'
        header, data, resized = fetcher.fetch_local(test_path)

        with open(os.path.join(test_path, 'libreto.thumb'), 'rb') as image_file:
            result_data = image_file.read()

        self.assertEqual(header, {'Content-Length': 2282, 'Content-Type': 'image/jpeg'})
        self.assertEqual(result_data, data)

        self.assertTrue(resized)

    def test_fetch_local_without_resizing(self):
        fetcher = album_art_fetcher.AlbumArtFetcher()
        test_path = '/usr/src/app/cherrymusic/apps/core/tests/not_resize'
        header, data, resized = fetcher.fetch_local(test_path)

        with open(os.path.join(test_path, 'cover.jpg'), 'rb') as image_file:
            result_data = image_file.read()

        self.assertEqual(header, {'Content-Length': 11814, 'Content-Type': 'image/jpeg'})
        self.assertEqual(result_data, data)

        self.assertFalse(resized)