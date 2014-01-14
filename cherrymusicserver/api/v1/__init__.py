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

import json
import cherrypy
import codecs
import sys
try:
    from urllib.parse import unquote
except ImportError:
    from backport.urllib.parse import unquote
try:
    from urllib import parse
except ImportError:
    from backport.urllib import parse


import audiotranscode

from cherrymusicserver import userdb
from cherrymusicserver import log
from cherrymusicserver import albumartfetcher
from cherrymusicserver import service
from cherrymusicserver.cherrymodel import MusicEntry
from cherrymusicserver.pathprovider import databaseFilePath, readRes
from cherrymusicserver.pathprovider import albumArtFilePath
import cherrymusicserver as cherry
import cherrymusicserver.metainfo as metainfo
from cherrymusicserver.util import Performance
import time

debug = True


class RESTResource(object):
    def __init__(self, root):
        self.root = root
    
    def url(components):
        resourcename = self.__class__.__name__.lower()
        return '/'.join([self.root.rootpath, resourcename] + components)
    
    exposed = True
    #@cherrypy.expose
    def default(self, *vpath, **params):
        return cherrypy.request.method
        try:
            method = getattr(self, cherrypy.request.method)
            return method(*vpath, **params)
        except AttributeError:
            raise cherrypy.HTTPError(405, "Method not implemented.")

    def parsepath(self, vpath, numargs):
        args = list(vpath)
        args += [None] * (numargs - len(vpath))
        return args
    
    def format_return(self, params, items):
        retformat = params.get('format', 'json')
        if retformat == 'html':
            return self.to_html(items)
        else: # default to json
            return self.to_json(items)
    
    def to_html(self, items):
        htmllist = ['<a href="'+i['url']+'">'+json.dumps(i['data'])+'</a>' for i in items]
        return '<ul><li>'+'</li><li>'.join(htmllist)+'</li></ul>'
    
    def to_json(self, items):
        itemtype = type(items)
        if itemtype == filter or itemtype == map:
            items = list(items)
        return json.dumps(items)


class Media(RESTResource):
    def GET(self, *vpath, **params):
        pass

@service.user(playlistdb='playlist', userdb='users')
class Playlist(RESTResource):
    
    def GET(self, *vpath, **params):
        self.root.requireAuth(params)
        username, playlistid = self.parsepath(vpath, 2)
        if username:
            userid = self.userdb.getIdByName(username)
            if userid == -1:
                raise HTTPError(404, 'No such user.')
            if playlistid:
                # get specific playlist
                playlistid = int(playlistid)
                playlist = self.playlistdb.loadPlaylist(playlistid, userid)
                simple_playlist = [track.to_dict() for track in playlist]
                simple_playlist = map(self.playlist_legacy_to_rest, simple_playlist)
                return self.format_return(params, simple_playlist)
            else:
                # get playlists by user
                
                # hack: replace legacy api later by proper db calls
                all_playlists = self.oldapi.api_showplaylists()
                all_playlists = map(self.listing_legacy_to_rest, all_playlists)
                by_user = lambda pl: pl['data']['userid'] == userid
                user_playlists = filter(by_user, all_playlists)
                # hack end
                return self.format_return(params, user_playlists)
        else:
            # hack: replace legacy api later by proper db calls
            all_playlists = self.root.oldapi.api_showplaylists()
            all_playlists = map(self.listing_legacy_to_rest, all_playlists)
            # hack end
            return self.format_return(params, all_playlists)

    def playlist_legacy_to_rest(self, plitem):
        """wrapper function to turn a legacy playlist into the new
        style restful playlist"""
        return {'data': plitem, 'url': '/serve/'+plitem['urlpath']}

    def listing_legacy_to_rest(self, pl):
        """wrapper function to turn a legacy listing of playlists into
        the new style restful playlist"""
        return {'data': pl, 'url': self.url([pl['username'], str(pl['plid'])])}

class User(RESTResource):
    def GET(self, *vpath, **params):
        username = self.parsepath(vpath, 1)
        if username:
            return 'user info'
        else:
            return 'user list'


class Session(RESTResource):
    def POST(self, *vpath, **params):
        #login
        pass

    def PUT(self, *vpath, **params):
        #save session
        pass

    def DELETE(self, *vpath, **params):
        # logout
        pass


class Config(RESTResource):
    def GET(self, *vpath, **params):
        username = self.parsepath(vpath, 1)
        if username:
            # get server config and user options
            pass
        else:
            # get server config
            pass


class Search(RESTResource):
    def GET(self, *vpath, **params):
        all_fields = ["playlist", "collection", "tracks"]
        query = params.get('q', None)
        fieldstrs = params.get('fields', '')
        fields = [f.strip() for f in fieldstrs.split(',') if f in all_fields]
        if len(fields) == 0:
            fields = all_fields
        pass


class Heartbeat(RESTResource):
    def GET(self, *vpath, **params):
        pass


class AlbumArt(RESTResource):
    def GET(self, *vpath, **params):
        pass

@service.user(model='cherrymodel', playlistdb='playlist',
              useroptions='useroptions', userdb='users')
class RestV1Root(object):
    exposed = True
    def __init__(self, config, oldapi, rootpath):
        self.config = config
        # injecting old api for easier implementation
        # should be handled less hackish later
        self.oldapi = oldapi
        self.rootpath = rootpath
    
        self.playlist = Playlist(self)
        self.albumart = AlbumArt()
        self.media = Media()
        self.user = User()
        self.session = Session()
        self.config = Config()
        self.search = Search()
        self.heartbeat = Heartbeat()
    
    def requireAuth(params={}):
        if 'token' in params:
            if params['token'] != 5:
                raise cherrypy.HTTPError(401, 'Unauthorized')
        elif not self.oldapi.isAuthorized():
            raise cherrypy.HTTPError(401, 'Unauthorized')
