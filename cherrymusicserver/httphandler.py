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

"""This class provides the api to talk to the client.
It will then call the cherrymodel, to get the 
requested information"""

import os #shouldn't have to list any folder in the future!
import sys
import json
import cherrypy
import codecs
from urllib.parse import unquote

from cherrymusicserver import renderjson
from cherrymusicserver import transcode
from cherrymusicserver import userdb
from cherrymusicserver import playlistdb
from cherrymusicserver import log
from cherrymusicserver.cherrymodel import MusicEntry
from cherrymusicserver.util import databaseFilePath, readRes
import cherrymusicserver as cherry
import cherrymusicserver.metainfo as metainfo

from urllib import parse

debug = True

class HTTPHandler(object):
    def __init__(self, config, model):
        self.model = model
        self.config = config
        self.jsonrenderer = renderjson.JSON()
        
        template_main = 'res/main.html'
        template_login = 'res/login.html'
        template_firstrun = 'res/firstrun.html'
        
        self.mainpage = readRes(template_main)
        self.loginpage = readRes(template_login)
        self.firstrunpage = readRes(template_firstrun)
        self.userdb = userdb.UserDB(databaseFilePath('user.db'))
        self.playlistdb = playlistdb.PlaylistDB(databaseFilePath('playlist.db'))
        
        self.handlers = {
            'search' : self.api_search,
            'rememberplaylist' : self.api_rememberplaylist,
            'saveplaylist' : self.api_saveplaylist,
            'loadplaylist': self.api_loadplaylist,
            'deleteplaylist' : self.api_deleteplaylist,
            'getmotd' : self.api_getmotd,
            'restoreplaylist' : self.api_restoreplaylist,
            'getplayables' : self.api_getplayables,
            'getuserlist' : self.api_getuserlist,
            'adduser' : self.api_adduser,
            'showplaylists' : self.api_showplaylists,
            'logout' : self.api_logout,
            'downloadpls' : self.api_downloadpls,
            'downloadm3u' : self.api_downloadm3u,
            'getsonginfo' : self.api_getsonginfo,
        }

    def issecure(self, url):
        return parse.urlparse(url).scheme == 'https'

    def getSecureUrl(self, url):
        u = parse.urlparse(url).netloc
        ip = u[:u.index(':')]
        return 'https://' + ip + ':' + cherry.config.server.ssl_port.str

    def index(self, action='', value='', filter='', login=None, username=None, password=None):

        if cherry.config.server.enable_ssl.bool and not self.issecure(cherrypy.url()):
            log.d('Not secure, redirecting...')
            raise cherrypy.HTTPRedirect(self.getSecureUrl(cherrypy.url()), 302)

        firstrun = 0 == self.userdb.getUserCount();
        if debug:
            #reload pages everytime in debig mode
            self.mainpage = readRes('res/main.html')
            self.loginpage = readRes('res/login.html')
            self.firstrunpage = readRes('res/firstrun.html')
        if login == 'login':
            self.session_auth(username, password)
            if cherrypy.session['username']:
                log.i('user ' + cherrypy.session['username'] + ' just logged in.')
        elif login == 'create admin user':
            if firstrun:
                if username.strip() and password.strip():
                    self.userdb.addUser(username, password, True)
                    self.session_auth(username, password)
                    return self.mainpage
            else:
                return "No, you can't."
        if firstrun:
                return self.firstrunpage
        else:
            if cherrypy.session.get('username', None):
                return self.mainpage
            else:
                return self.loginpage
    index.exposed = True

    def session_auth(self, username, password):
        user = self.userdb.auth(username, password)
        cherrypy.session['username'] = user.name
        cherrypy.session['userid'] = user.uid
        cherrypy.session['admin'] = user.isadmin
        
    def getUserId(self):
        try:
            return cherrypy.session['userid']
        except KeyError:
            cherrypy.lib.sessions.expire()
            cherrypy.HTTPRedirect(cherrypy.url(), 303)
            return ''
            
    def trans(self, *args):
        if len(args):
            newformat = args[-1][4:] #get.format
            path = '/'.join(args[:-1])
            fullpath = os.path.join(cherry.config.media.basedir.str, path)
            cherrypy.response.headers["Content-Type"] = transcode.getMimeType(newformat)            
            return transcode.transcode(fullpath, newformat, usetmpfile=True)
    trans.exposed = True
    trans._cp_config = {'response.stream': True}

    def api(self, action='', value='', filter=''):
        if action in self.handlers:
            return self.handlers[action](value)
        #todo: clean this mess:
        else:
            dirtorender = value
            dirtorenderabspath = os.path.join(cherry.config.media.basedir.str, value)
            if os.path.isdir(dirtorenderabspath):
                if action == 'compactlistdir':
                    return self.jsonrenderer.render(self.model.listdir(dirtorender, filter))
                else: #if action=='listdir':
                    return self.jsonrenderer.render(self.model.listdir(dirtorender))
            else:
                return 'Error rendering dir [action: "' + action + '", value: "' + value + '"]'
    api.exposed = True
    
    def api_search(self, value):
        if not value.strip():
            return self.jsonrenderer.render([MusicEntry(path="if you're looking for nothing, you'll be getting nothing",repr="")])
        return self.jsonrenderer.render(self.model.search(value.strip()))
        
    def api_rememberplaylist(self, value):
        pl = json.loads(value)
        cherrypy.session['playlist'] = pl['playlist']
        
    def api_saveplaylist(self, value):
        pl = json.loads(value)
        return self.playlistdb.savePlaylist(
            userid=self.getUserId(),
            public=1 if pl['public'] else 0,
            playlist=pl['playlist'],
            playlisttitle=pl['playlistname']);
            
    def api_deleteplaylist(self, value):
        return self.playlistdb.deletePlaylist(value, self.getUserId())
            
    def api_loadplaylist(self,value):
        return  self.jsonrenderer.render(self.playlistdb.loadPlaylist(
                            playlistid=value,
                            userid=self.getUserId()
                ));
                
    def api_getmotd(self,value):
        return self.model.motd()
        
    def api_restoreplaylist(self,value):
        return json.dumps(cherrypy.session.get('playlist', []))
        
    def api_getplayables(self,value):
        return json.dumps(cherry.config.media.playable.list)
        
    def api_getuserlist(self,value):
        if cherrypy.session['admin']:
            return json.dumps(self.userdb.getUserList())
        else:
            return {'id':'-1', 'username':'nobody', 'admin':0}
    
    def api_adduser(self, value):
        if cherrypy.session['admin']:
            new = json.loads(value)
            return self.userdb.addUser(new['username'], new['password'], new['isadmin'])
        else:
            return "You didn't think that would work, did you?"

    def api_showplaylists(self,value):
        playlists = self.playlistdb.showPlaylists(self.getUserId())
        #translate userids to usernames:
        for pl in playlists:
            pl['username']=self.userdb.getNameById(pl['userid'])
        return json.dumps(playlists);
        
    def api_logout(self,value):
        cherrypy.lib.sessions.expire()
        
    def api_downloadpls(self,value):
        dlval = json.loads(value)
        pls = self.playlistdb.createPLS(dlval['plid'],self.getUserId(),dlval['addr'])
        name = self.playlistdb.getName(value,self.getUserId())
        if pls and name:
            return self.serve_string_as_file(pls,name+'.pls')
            
    def api_downloadm3u(self,value):
        dlval = json.loads(value)
        pls = self.playlistdb.createM3U(dlval['plid'],self.getUserId(),dlval['addr'])
        name = self.playlistdb.getName(value,self.getUserId())
        if pls and name:
            return self.serve_string_as_file(pls,name+'.m3u')       
            
    def api_getsonginfo(self,value):
        #TODO yet another dirty hack. removing the /serve thing is a mess.
        abspath = os.path.join(cherry.config.media.basedir.str,unquote(value)[7:])
        return json.dumps(metainfo.getSongInfo(abspath).dict())
    
    def serve_string_as_file(self,string,filename):
        cherrypy.response.headers["Content-Type"] = "application/x-download"
        cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="'+filename+'"'
        return codecs.encode(string,"UTF-8")
