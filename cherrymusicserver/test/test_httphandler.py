#!/usr/bin/env python3
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

from mock import *
import unittest

import json

from contextlib import contextmanager

import cherrymusicserver as cherry

from cherrymusicserver import configuration
cherry.config = configuration.from_defaults()

from cherrymusicserver import httphandler
from cherrymusicserver import service
from cherrymusicserver.cherrymodel import CherryModel, MusicEntry

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

from cherrymusicserver.playlistdb import PlaylistDB
MockPlaylistDB = Mock(spec=PlaylistDB)
service.provide('playlist', MockPlaylistDB)


@contextmanager
def mock_auth():
    ''' Context where user 1 is logged in '''
    always_auth = lambda _: True
    root_id = lambda _: 1
    with patch('cherrymusicserver.httphandler.HTTPHandler.isAuthorized', always_auth):
        with patch('cherrymusicserver.httphandler.HTTPHandler.getUserId', root_id):
            yield


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

    def call_api(self, action, **data):
        with mock_auth():
            return self.http.api(action, data=json.dumps(data))



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
        try:
            print(self.call_api('deleteplaylist', playlistid=13))
        except httphandler.cherrypy.HTTPError as e:
            print(e)
        MockPlaylistDB.deletePlaylist.assert_called_with(13, ANY, override_owner=False)

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

    def test_api_downloadpls_call(self):
        MockPlaylistDB.getName.return_value = 'some_playlist_name'
        MockPlaylistDB.createPLS.return_value = 'some_pls_string'

        self.call_api('downloadpls', plid=13, hostaddr='host')

        MockPlaylistDB.createPLS.assert_called_with(userid=ANY, plid=13, addrstr='host')


    def test_api_downloadm3u_call(self):
        MockPlaylistDB.getName.return_value = 'some_playlist_name'
        MockPlaylistDB.createM3U.return_value = 'some_m3u_string'

        self.call_api('downloadm3u', plid=13, hostaddr='host')

        MockPlaylistDB.createM3U.assert_called_with(userid=ANY, plid=13, addrstr='host')


    def test_api_export_playlists(self):
        from collections import defaultdict
        MockPlaylistDB.showPlaylists.return_value = [defaultdict(MagicMock)]
        MockPlaylistDB.getName.return_value = 'some_playlist_name'
        MockPlaylistDB.createM3U.return_value = 'some_m3u_string'

        with patch('cherrypy.session', {'userid': 1}, create=True):
            bytestr = self.http.export_playlists(hostaddr='hostaddr', format='m3u')

        import io, zipfile
        zip = zipfile.ZipFile(io.BytesIO(bytestr), 'r')
        try:
            badfile = zip.testzip()
            assert badfile is None
            filenames = zip.namelist()
            assert ['some_playlist_name.m3u'] == filenames, filenames
            content = zip.read('some_playlist_name.m3u')
            assert 'some_m3u_string'.encode('ASCII') == content, content
        finally:
            zip.close()

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

    def test_api_userdelete_needs_auth(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'userdelete')

    def test_api_userdelete_call(self):
        session = {'userid': 1, 'admin': True}
        userdb = Mock()
        with patch('cherrypy.session', session, create=True):
            with patch('cherrymusicserver.service.get') as service:
                service.return_value = userdb
                self.call_api('userdelete', userid=13)
        userdb.deleteUser.assert_called_with(13)

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
        self.assertRaises(AttributeError, self.http.api, 'listdir')

    def test_api_listdir_must_call_cherrymodel_listdir(self):
        mock = MagicMock(spec=CherryModel)
        oldservice = service.get('cherrymodel')
        service.provide('cherrymodel', mock)

        self.http.api_listdir('dir')
        mock.listdir.assert_called_with('dir')

        service.provide('cherrymodel', oldservice)

    def test_api_compactlistdir_must_call_cherrymodel_listdir(self):
        mock = MagicMock(spec=CherryModel)
        oldservice = service.get('cherrymodel')
        service.provide('cherrymodel', mock)

        self.http.api_compactlistdir('dir', filterstr='x')
        mock.listdir.assert_called_with('dir', 'x')

        service.provide('cherrymodel', oldservice)

    def test_api_userchangepassword(self):
        """when attribute error is raised, this means that cherrypy
        session is used to authenticate the http request."""
        self.assertRaises(AttributeError, self.http.api, 'userchangepassword')

    def test_trans(self):
        import os
        config = {'media.basedir': 'BASEDIR', 'media.transcode': True}
        with mock_auth():
            with patch('cherrymusicserver.httphandler.cherry.config', config):
                with patch('cherrymusicserver.httphandler.cherrypy'):
                    with patch('cherrymusicserver.httphandler.audiotranscode.AudioTranscode') as transcoder:
                        transcoder.return_value = transcoder
                        expectPath = os.path.join(config['media.basedir'], 'path')

                        httphandler.HTTPHandler(config).trans('newformat', 'path', bitrate=111)

                        transcoder.transcode_stream.assert_called_with(expectPath, 'newformat', bitrate=111, starttime=0)


if __name__ == "__main__":
    unittest.main()
