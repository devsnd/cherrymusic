"""This class provides the api to talk to the client.
It will then call the cherrymodel, to get the 
requested information"""

import os #shouldn't have to list any folder in the future!
import json
import cherrypy

from cherrymusic import renderjson
from cherrymusic import userdb
from cherrymusic import playlistdb

debug = True


class HTTPHandler(object):
    def __init__(self, config, model):
        self.model = model
        self.config = config
        self.jsonrenderer = renderjson.JSON()
        self.mainpage = open('res/main.html').read()
        self.loginpage = open('res/login.html').read()
        self.firstrunpage = open('res/firstrun.html').read()
        self.userdb = userdb.UserDB()
        self.playlistdb = playlistdb.PlaylistDB()

    def index(self, action='', value='', filter='', login=None, username=None, password=None):
        firstrun = 0 == self.userdb.getUserCount();
        if debug:
            #reload pages everytime in debig mode
            self.mainpage = open('res/main.html').read()
            self.loginpage = open('res/login.html').read()
            self.firstrunpage = open('res/firstrun.html').read()
        if login == 'login':
            self.session_auth(username,password)
            if cherrypy.session['username']:
                print('user '+cherrypy.session['username']+' just logged in.')
        elif login == 'create admin user':
            if firstrun:
                if username.strip() and password.strip():
                    self.userdb.addUser(username, password, True)
                    self.session_auth(username,password)
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
        userid, authuser, isadmin = self.userdb.auth(username,password)
        cherrypy.session['username'] = authuser
        cherrypy.session['userid'] = userid
        cherrypy.session['admin'] = isadmin

    def api(self, action='', value='', filter=''):
        return self.handle(self.jsonrenderer, action, value, filter)
    api.exposed = True
    
    def handle(self, renderer, action, value, filter):
        if action=='search':
            if not value.strip():
                return """<span style="width:100%; text-align: center; float: left;">if you're looking for nothing, you'll be getting nothing.</span>"""
            return renderer.render(self.model.search(value.strip()))
        elif action == 'getmotd':
            return self.model.motd()
        elif action == 'rememberplaylist':
            pl = json.loads(value)
            cherrypy.session['playlist'] = pl['playlist']
        elif action == 'restoreplaylist':
            return json.dumps(cherrypy.session.get('playlist',[]))
        elif action == 'saveplaylist':
            pl = json.loads(value)
            return self.playlistdb.savePlaylist(
                userid = cherrypy.session['userid'],
                public = 1 if pl['public'] else 0,
                playlist = pl['playlist'],
                playlisttitle = pl['playlistname']);
        elif action == 'loadplaylist':
            return  json.dumps(self.playlistdb.loadPlaylist(
                                playlistid=value,
                                userid=cherrypy.session['userid']
                    ));
        elif action == 'showplaylists':
            return json.dumps(self.playlistdb.showPlaylists(cherrypy.session['userid']));
        elif action == 'logout':
            cherrypy.lib.sessions.expire()
        elif action == 'getuserlist':
            if cherrypy.session['admin']:
                return json.dumps(self.userdb.getUserList())
            else:
                return {'id':'-1','username':'nobody','admin':0}
        elif action == 'adduser':
            if cherrypy.session['admin']:
                new = json.loads(value)
                return self.userdb.addUser(new['username'],new['password'],new['isadmin'])
            else:
                return "You didn't think that would work, did you?"
        else:
            dirtorender = value
            dirtorenderabspath = os.path.join(self.config.config[self.config.BASEDIR],value)
            if os.path.isdir(dirtorenderabspath):
                if action=='compactlistdir':
                    return renderer.render(self.model.listdir(dirtorender,filter))
                else: #if action=='listdir':
                    return renderer.render(self.model.listdir(dirtorender))
            else:
                return 'Error rendering dir [action: "'+action+'", value: "'+value+'"]'