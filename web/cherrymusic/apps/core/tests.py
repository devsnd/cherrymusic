from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth.forms import AuthenticationForm
from cherrymusic.apps.core.models import User

class UsernameCaseInsensitiveTests(TestCase):

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
        try:
            user = User.objects.create_user('Temporary', 'temporary@temporary.com', 'temporary')
            self.fail("User exception not thrown")
        except IntegrityError:
            pass

## AlbumArtFetecher

#from __future__ import unicode_literals
#
#import nose
#
#from mock import *
#from nose.tools import *
#from cherrymusicserver.test import helpers
#
#from binascii import unhexlify
#
#from cherrymusicserver import log
#log.setTest()
#
#from cherrymusicserver import albumartfetcher
#
#def test_methods():
#    for method in albumartfetcher.AlbumArtFetcher.methods:
#        yield try_method, method
#
#def try_method(method, timeout=15):
#    fetcher = albumartfetcher.AlbumArtFetcher(method=method, timeout=timeout)
#    results = fetcher.fetchurls('best of')
#    results += fetcher.fetchurls('best of')    # once is not enough sometimes (?)
#    ok_(results, "method {0!r} results: {1}".format(method, results))
#
#
#def test_fetchLocal_id3():
#    """Album art can be fetched with tinytag"""
#
#    # PNG image data, 1 x 1, 1-bit grayscale, non-interlaced
#    _PNG_IMG_DATA = unhexlify(b''.join(b"""
#    8950 4e47 0d0a 1a0a 0000 000d 4948 4452
#    0000 0001 0000 0001 0100 0000 0037 6ef9
#    2400 0000 1049 4441 5478 9c62 6001 0000
#    00ff ff03 0000 0600 0557 bfab d400 0000
#    0049 454e 44ae 4260 82""".split()))
#
#    fetcher = albumartfetcher.AlbumArtFetcher()
#    with patch('cherrymusicserver.albumartfetcher.TinyTag') as TinyTagMock:
#        TinyTagMock.get().get_image.return_value = _PNG_IMG_DATA
#        with helpers.tempdir('test_albumartfetcher') as tmpd:
#            artpath = helpers.mkpath('test.mp3', parent=tmpd)
#            fetcher.fetchLocal(tmpd)
#
#    TinyTagMock.get.assert_called_with(artpath, image=True)
#    assert TinyTagMock.get().get_image.called