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
import audiotranscode

from cherrymusicserver import renderjson
from cherrymusicserver import userdb
from cherrymusicserver import playlistdb
from cherrymusicserver import log
from cherrymusicserver import albumartfetcher
from cherrymusicserver.cherrymodel import MusicEntry
from cherrymusicserver.util import databaseFilePath, readRes
import cherrymusicserver as cherry
import cherrymusicserver.metainfo as metainfo
from cherrymusicserver.util import Performance
from cherrymusicserver import useroptiondb
import time

from urllib import parse

debug = True

class HTTPHandler(object):
    def __init__(self, config, model):
        self.model = model
        self.config = config
        self.useroptions = useroptiondb.UserOptionDB(databaseFilePath('useroptions.db'))
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
            'fastsearch' : self.api_fastsearch,
            'rememberplaylist' : self.api_rememberplaylist,
            'saveplaylist' : self.api_saveplaylist,
            'loadplaylist': self.api_loadplaylist,
            'deleteplaylist' : self.api_deleteplaylist,
            'getmotd' : self.api_getmotd,
            'restoreplaylist' : self.api_restoreplaylist,
            'getplayables' : self.api_getplayables,
            'getuserlist' : self.api_getuserlist,
            'adduser' : self.api_adduser,
            'userdelete' : self.api_userdelete,
            'showplaylists' : self.api_showplaylists,
            'logout' : self.api_logout,
            'downloadpls' : self.api_downloadpls,
            'downloadm3u' : self.api_downloadm3u,
            'getsonginfo' : self.api_getsonginfo,
            'getencoders' : self.api_getencoders,
            'getdecoders' : self.api_getdecoders,
            'transcodingenabled': self.api_transcodingenabled,
            'updatedb' : self.api_updatedb,
            'getconfiguration' : self.api_getconfiguration,
            'compactlistdir' : self.api_compactlistdir,
            'listdir' : self.api_listdir,
            'fetchalbumart' : self.api_fetchalbumart,
            'heartbeat' : self.api_heartbeat,
            'getuseroptions' : self.api_getuseroptions,
            'opensearchdescription' : self.api_opensearchdescription,
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
            if self.isAuthorized():
                return self.mainpage
            else:
                return self.loginpage
    index.exposed = True
    
    def isAuthorized(self):
        return cherrypy.session.get('username', None) or self.autoLoginEnabled()
    
    def autoLoginEnabled(self):
        if cherrypy.request.remote.ip == '127.0.0.1' and cherry.config.server.localhost_auto_login.bool:
            cherrypy.session['username'] = self.userdb.getNameById(1)
            cherrypy.session['userid'] = 1
            cherrypy.session['admin'] = True
            return True
        return False

    def session_auth(self, username, password):
        user = self.userdb.auth(username, password)
        if user.isadmin and not cherry.config.server.permit_remote_admin_login and not cherrypy.request.remote.ip == '127.0.0.1':
            user = userdb.User.nobody()
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
        if not self.isAuthorized():
            raise cherrypy.HTTPRedirect('http://'+parse.urlparse(cherrypy.url()).netloc, 302)
        if cherry.config.media.transcode and len(args):
            newformat = args[-1][4:] #get.format
            path = os.path.sep.join(args[:-1])
            fullpath = os.path.join(cherry.config.media.basedir.str, path)
            cherrypy.response.headers["Content-Type"] = audiotranscode.getMimeType(newformat)
            return audiotranscode.getTranscoded(fullpath, newformat, usetmpfile=True)
    trans.exposed = True
    trans._cp_config = {'response.stream': True}

    def api(self, *args, **kwargs):
        if not self.isAuthorized():
            raise cherrypy.HTTPRedirect('http://'+parse.urlparse(cherrypy.url()).netloc, 302)
        action = args[0] if args else ''
        value=kwargs.get('value','')
        if not value and len(args)>1:
            value = map(unquote,args[1:len(args)])
            if len(value) == 1:
                value = value[0]
        #filter_str=kwargs.get('filter','')
        if action in self.handlers:
            return self.handlers[action](value)
        else:
            return "Error: no such action."
        self.api_getuseroptions(None)
    api.exposed = True

    def api_opensearchdescription(self, value):
        return """<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
 <ShortName>CherryMusic</ShortName>
 <Description>open source streaming server</Description>
 <Tags>cherrymusic open source streaming server python mp3 jplayer</Tags>
 <Url type="text/html" template="{} {{searchTerms}}"/>
</OpenSearchDescription>""".format(cherrypy.url())

    def api_getuseroptions(self, value):
        uo = self.useroptions.forUser(self.getUserId())
        uco = uo.getChangableOptions()
        return json.dumps(uco)
        
    def api_heartbeat(self, value):
        uo = self.useroptions.forUser(self.getUserId())
        uo.setOption('last_time_online', int(time.time()))

    def api_fetchalbumart(self, value):
        cherrypy.session.release_lock()
        if cherry.config.media.fetch_album_art.bool:
            params = json.loads(value)
            directory = params['directory']
            album = os.path.basename(directory)
            artist = os.path.basename(os.path.dirname(directory))
            keywords = artist+' '+album
            log.i("Fetching album art for keywords '%s'" % keywords)
            fetcher = albumartfetcher.AlbumArtFetcher()
            header, data = fetcher.fetch(keywords)
            if header:
                cherrypy.response.headers["Content-Type"] = header['Content-Type']
                cherrypy.response.headers["Content-Length"] = header['Content-Length']
                return data
            cherrypy.response.headers["Content-Length"] = 0
            return ''
    
    def api_compactlistdir(self, value):
        params = json.loads(value)
        dirtorender = params['directory']
        dirtorenderabspath = os.path.join(cherry.config.media.basedir.str, dirtorender)
        if os.path.isdir(dirtorenderabspath):
            return self.jsonrenderer.render(self.model.listdir(dirtorender, params['filter']))
        else:
            return "Error rendering getting results. Request doesn't lead to a directory"
    
    def api_listdir(self,value):
        if value:
            params = json.loads(value)
            dirtorender = params['directory']
        else:
            dirtorender = ''
        dirtorenderabspath = os.path.join(cherry.config.media.basedir.str, dirtorender)
        if os.path.isdir(dirtorenderabspath):            
            return self.jsonrenderer.render(self.model.listdir(dirtorender))
        else:
            return "Error rendering getting results. Request doesn't lead to a directory"
    
    def api_search(self, value, isFastSearch=False):
        if not value.strip():
            return self.jsonrenderer.render([MusicEntry(path="if you're looking for nothing, you'll be getting nothing",repr="")])
        with Performance('processing whole search request'):
            searchresults = self.model.search(value.strip(),isFastSearch)
            with Performance('rendering search results as json'):
                return self.jsonrenderer.render(searchresults)
        
    def api_fastsearch(self, value):
        return self.api_search(value,True)
    
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
        session_playlist = cherrypy.session.get('playlist', [])
        session_playlist = list(filter(lambda x : x != None, session_playlist))
        return json.dumps(session_playlist)
        
    def api_getplayables(self,value):
        return json.dumps(cherry.config.media.playable.list)
    
    def api_getuserlist(self,value):
        if cherrypy.session['admin']:
            userlist = self.userdb.getUserList()
            for user in userlist:
                user['last_time_online'] = self.useroptions.forUser(user['id']).getOptionValue('last_time_online')
            return json.dumps(userlist)
        else:
            return json.dumps([])
    
    def api_adduser(self, value):
        if cherrypy.session['admin']:
            new = json.loads(value)
            return self.userdb.addUser(new['username'], new['password'], new['isadmin'])
        else:
            return "You didn't think that would work, did you?"

    def api_userdelete(self, value):
        params = json.loads(value)
        if cherrypy.session['admin'] and cherrypy.session['userid'] != params['userid']:
            return 'success' if self.userdb.deleteUser(params['userid']) else 'failed'
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
        
    def api_getencoders(self, value):
        return json.dumps(audiotranscode.getEncoders())
        
    def api_getdecoders(self, value):
        return json.dumps(audiotranscode.getDecoders())
    
    def api_transcodingenabled(self,value):
        return json.dumps(cherry.config.media.transcode.bool)
        
    def api_updatedb(self,value):
        self.model.updateLibrary()
        return 'success'
    
    def api_getconfiguration(self, value):
        clientconfigkeys = {
            'getencoders' : audiotranscode.getEncoders(),
            'getdecoders' : audiotranscode.getDecoders(),
            'transcodingenabled' : cherry.config.media.transcode.bool,
            'getplayables' : cherry.config.media.playable.list,
            'fetchalbumart' : cherry.config.media.fetch_album_art.bool,
        }
        retval = {}
        for configkey in json.loads(value):
            if configkey in clientconfigkeys:
                retval[configkey] = clientconfigkeys[configkey]
        return json.dumps(retval)
            
    
    def serve_string_as_file(self,string,filename):
        cherrypy.response.headers["Content-Type"] = "application/x-download"
        cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="'+filename+'"'
        return codecs.encode(string,"UTF-8")
