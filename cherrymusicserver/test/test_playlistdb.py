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

import nose

from mock import *
from nose.tools import *

from cherrymusicserver import log
log.setTest()

from cherrymusicserver import database
from cherrymusicserver import service

from cherrymusicserver.playlistdb import *


_DEFAULT_USERID = 1


def setup():
    service.provide('dbconnector', database.sql.TmpConnector)
    database.ensure_current_version(DBNAME)


def teardown():
    service.provide('dbconnector', None)


def create_playlist(name, titles):
    pldb = PlaylistDB()
    public = True
    userid = _DEFAULT_USERID
    songs = [dict(title=t, url="url(" + t + ")") for t in titles]
    pldb.savePlaylist(userid, public, songs, name, overwrite=True)
    playlist = get_playlist(name)
    assert playlist
    return playlist

def test_delete_playlist():
    pldb = PlaylistDB()
    create_playlist('deleteme', ['delete', 'me'])
    pl = get_playlist('deleteme')
    assert pldb.deletePlaylist(pl['plid'], None, override_owner=True) == 'success'
    assert pldb.deletePlaylist(pl['plid'], None, override_owner=True) == "This playlist doesn't exist! Nothing deleted!"

def get_playlist(name):
    pldb = PlaylistDB()
    for p in pldb.showPlaylists(_DEFAULT_USERID):
        if p['title'] == name:
            return p

def test_set_public():
    pl = create_playlist('some_title', list('abc'))
    assert get_playlist('some_title')['public']

    PlaylistDB().setPublic(_DEFAULT_USERID, pl['plid'], False)

    assert not get_playlist('some_title')['public']


if __name__ == '__main__':
    nose.runmodule()
