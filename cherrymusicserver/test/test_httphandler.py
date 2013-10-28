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

from cherrymusicserver import configuration
cherry.config = configuration.from_defaults()

from cherrymusicserver import httphandler
from cherrymusicserver import service
from cherrymusicserver.cherrymodel import MusicEntry

from cherrymusicserver import log

class MockAction(Exception):
    pass

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
    def updateLibrary(self):
        raise MockAction('updateLibrary')
service.provide('cherrymodel', MockModel)


class CherryPyMock:
    def __init__(self):
        self.session = {'admin': False}

class MockPlaylistDB:
    def __init__(self):
        pass

    def getName(self, val, userid):
        return str(val)+str(userid)
service.provide('playlist', MockPlaylistDB)


class TestHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.http = httphandler.HTTPHandler(cherry.config)
        for apicall, func in self.http.handlers.items():
            try:
                getattr(self,'test_'+func.__name__)
            except AttributeError:
                print('Missing test for api handler %s!' % func.__name__)

    def tearDown(self):
        pass

    def test_api_search(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'search')

    def test_api_fastsearch(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'search')

    def test_api_rememberplaylist(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'rememberplaylist')

    def test_api_saveplaylist(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'saveplaylist')
        
    def test_api_deleteplaylist(self):
        pass #needs to be tested in playlistdb

    def test_api_loadplaylist(self):
        pass #needs to be tested in playlistdb

    def test_api_getmotd(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getmotd')

    def test_api_restoreplaylist(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'restoreplaylist')

    def test_api_getplayables(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getplayables')
        
    def test_api_getuserlist(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getuserlist')
        
    def test_api_adduser(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'adduser')
        
    def test_api_showplaylists(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'showplaylists')

    def test_api_logout(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'logout')

    def test_api_downloadpls(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'downloadpls')

    def test_api_downloadm3u(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'downloadm3u')

    def test_api_getsonginfo(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getsonginfo')

    def test_api_getencoders(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getencoders')

    def test_api_getdecoders(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getdecoders')

    def test_api_transcodingenabled(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'transcodingenabled')
        
    def test_api_updatedb(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'updatedb')
        
    def test_api_compactlistdir(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'compactlistdir')
        
    def test_api_getconfiguration(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getconfiguration')
        
    def test_api_getuseroptions(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'getuseroptions')
        
    def test_api_userdelete(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'userdelete')
        
    def test_api_heartbeat(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'heartbeat')
        
    def test_api_fetchalbumart(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        if not self.http.handlers['fetchalbumart'].noauth:
            self.assertRaises(AttributeError, self.http.api, 'fetchalbumart')
        
    def test_api_setuseroption(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'setuseroption')
         
    def test_api_changeplaylist(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        if not self.http.handlers['fetchalbumart'].noauth:
            self.assertRaises(AttributeError, self.http.api, 'fetchalbumart')
            
    def test_api_listdir(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'changeplaylist')
        
    def test_api_userchangepassword(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'userchangepassword')



if __name__ == "__main__":
    unittest.main()
