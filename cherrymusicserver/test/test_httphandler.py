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

from cherrymusicserver import httphandler
from cherrymusicserver import configuration
from cherrymusicserver.cherrymodel import MusicEntry

from cherrymusicserver import log

    
class TestHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.http = httphandler.HTTPHandler(configuration.from_defaults(),MockModel())
        for apicall, func in self.http.handlers.items():
            try:
                getattr(self,'test_'+func.__name__)
            except AttributeError:
                print('Missing test for api handler %s!' % func.__name__)

    def tearDown(self):
        pass
        
    def test_api_search(self):
        self.http.api('search','asd')
       
"""    def test_api_search(self, value):
        self.http.api('search',
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
        
    def api_getencoders(self, value):
        return json.dumps(audiotranscode.getEncoders())
        
    def api_getdecoders(self, value):
        return json.dumps(audiotranscode.getDecoders())
    
    def api_transcodingenabled(self,value):
        return json.dumps(cherry.config.media.transcode.bool)
    
    def serve_string_as_file(self,string,filename):
        cherrypy.response.headers["Content-Type"] = "application/x-download"
        cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="'+filename+'"'
        return codecs.encode(string,"UTF-8")"""

class MockModel:
    def __init__(self):
        pass
    def search(self,value):
        return [MusicEntry('mock result','mock result')]

if __name__ == "__main__":
    unittest.main()