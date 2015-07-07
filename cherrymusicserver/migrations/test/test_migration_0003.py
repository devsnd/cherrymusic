#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2014 Tom Wallroth & Tilman Boerner
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

import nose

from mock import *
from nose.tools import *

from cherrymusicserver.test import helpers

import base64
import codecs
import hashlib
import os

from cherrymusicserver import pathprovider

from cherrymusicserver.migrations import migration_0003


def test_migration():
    tests = [
        ['empty dir',
            [],
            ['.hashpath']],
        ['migrated dir',
            ['.hashpath', _oldname('b/c')],
            ['.hashpath', _oldname('b/c')]],
        ['standard migration',
            [_oldname('a'), _oldname('b/c')],
            [_newname('a'), _newname('b/c'), '.hashpath']],
        ['hidden file',
            ['.foo', _oldname('b/c')],
            ['.foo', _newname('b/c'), '.hashpath']],
        ['invalid base64 encoding',
            ['badbase64='],
            ['badbase64=', '.hashpath']],
    ]
    for description, startnames, wantnames in tests:
        check_filelist.description = 'migration_0003 (albumart): ' + description
        yield check_filelist, startnames, wantnames


def check_filelist(startnames, wantnames):
    with helpers.tempdir('cherrymusic.test_migration_0003') as tmpd:
        artfolder = helpers.mkpath('art/', tmpd)
        for name in startnames:
            helpers.mkpath(name, artfolder)

        with patch('cherrymusicserver.pathprovider.albumArtFilePath', _mock_artpath(artfolder)):
            migration_0003.migrate()

        expected, result = sorted(wantnames), sorted(os.listdir(artfolder))
        eq_(expected, result, '\n%r\n%r' % (expected, result))


def _oldname(s):
    "copied from pathprovider"
    utf8_bytestr = codecs.encode(s, 'UTF-8')
    utf8_altchar = codecs.encode('+-', 'UTF-8')
    return codecs.decode(base64.b64encode(utf8_bytestr, utf8_altchar), 'UTF-8')

def _newname(s):
    utf8_bytestr = codecs.encode(s, 'UTF-8')
    return hashlib.md5(utf8_bytestr).hexdigest() + '.thumb'

_real_artpath = pathprovider.albumArtFilePath

def _mock_artpath(tmpd):
    return lambda s: os.path.join(tmpd, os.path.basename(_real_artpath(s)) if s else '')


if __name__ == '__main__':
    nose.runmodule()
