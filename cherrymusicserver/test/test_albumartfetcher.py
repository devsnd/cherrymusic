#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#
from __future__ import unicode_literals

import nose

from mock import *
from nose.tools import *
from cherrymusicserver.test import helpers

from binascii import unhexlify

from cherrymusicserver import log
log.setTest()

from cherrymusicserver import albumartfetcher

def test_methods():
    for method in albumartfetcher.AlbumArtFetcher.methods:
        yield try_method, method

def try_method(method, timeout=15):
    fetcher = albumartfetcher.AlbumArtFetcher(method=method, timeout=timeout)
    results = fetcher.fetchurls('best of')
    results += fetcher.fetchurls('best of')    # once is not enough sometimes (?)
    ok_(results, "method {0!r} results: {1}".format(method, results))


def test_fetchLocal_id3():
    """Album art can be fetched with tinytag"""

    # PNG image data, 1 x 1, 1-bit grayscale, non-interlaced
    _PNG_IMG_DATA = unhexlify(b''.join(b"""
    8950 4e47 0d0a 1a0a 0000 000d 4948 4452
    0000 0001 0000 0001 0100 0000 0037 6ef9
    2400 0000 1049 4441 5478 9c62 6001 0000
    00ff ff03 0000 0600 0557 bfab d400 0000
    0049 454e 44ae 4260 82""".split()))

    fetcher = albumartfetcher.AlbumArtFetcher()
    with patch('cherrymusicserver.albumartfetcher.TinyTag') as TinyTagMock:
        TinyTagMock.get().get_image.return_value = _PNG_IMG_DATA
        with helpers.tempdir('test_albumartfetcher') as tmpd:
            artpath = helpers.mkpath('test.mp3', parent=tmpd)
            fetcher.fetchLocal(tmpd)

    TinyTagMock.get.assert_called_with(artpath, image=True)
    assert TinyTagMock.get().get_image.called


if __name__ == '__main__':
    nose.runmodule()
