#!/usr/bin/python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 Tom Wallroth & Tilman Boerner
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

import unittest
import json

import cherrymusicserver as cherry

from cherrymusicserver import httphandler
from cherrymusicserver import configuration
from cherrymusicserver.cherrymodel import MusicEntry

from cherrymusicserver import log


class MockModel:
    def __init__(self):
        pass
    def search(self,value,isFastSearch=False):
        if isFastSearch:
            return [MusicEntry('fast mock result','fast mock result')]
        else:
            return [MusicEntry('mock result','mock result')]
    def motd(self):
        return "motd"

class CherryPyMock:
    def __init__(self):
        self.session = {'admin': False}

class MockPlaylistDB:
    def __init__(self):
        pass

    def getName(self, val, userid):
        return str(val)+str(userid)

class TestHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.playlistdb = MockPlaylistDB()
        cherry.config = configuration.from_defaults()
        self.http = httphandler.HTTPHandler(cherry.config,MockModel())
        for apicall, func in self.http.handlers.items():
            try:
                getattr(self,'test_'+func.__name__)
            except AttributeError:
                print('Missing test for api handler %s!' % func.__name__)

    def tearDown(self):
        pass

    def test_api_search(self):
        self.http.api(action='search',value='asd')

    def test_api_fastsearch(self):
        res = self.http.api(action='fastsearch',value='asd')

    def test_api_rememberplaylist(self):
        pass #relies on cherrypy session

    def test_api_saveplaylist(self):
        pass #needs to be tested in playlistdb

    def test_api_deleteplaylist(self):
        pass #needs to be tested in playlistdb

    def test_api_loadplaylist(self):
        pass #needs to be tested in playlistdb

    def test_api_getmotd(self):
        self.http.api(action='getmotd')

    def test_api_restoreplaylist(self):
        pass #relies on cherrypy session
        #self.http.api(action='restoreplaylist')

    def test_api_getplayables(self):
        p = self.http.api(action='getplayables')
        self.assertEqual(p, json.dumps(self.http.config.media.playable.str.split(' ')))

    def test_api_getuserlist(self):
        pass #relies on cherrypy session

    def test_api_adduser(self):
        pass #relies on cherrypy session

    def test_api_showplaylists(self):
        pass #needs to be tested in playlist tests

    def test_api_logout(self):
        pass #relies on cherrypy session

    def test_api_downloadpls(self):
        pass #untestable

    def test_api_downloadm3u(self):
        pass #untestable

    def test_api_getsonginfo(self):
        pass #relies on config.media.basedir

    def test_api_getencoders(self):
        pass #relies on audiotranscode

    def test_api_getdecoders(self):
        pass #relies on audiotranscode

    def test_api_transcodingenabled(self):
        self.assertEqual(self.http.api(action='transcodingenabled'),'false')


if __name__ == "__main__":
    unittest.main()
