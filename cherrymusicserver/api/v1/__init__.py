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

from cherrymusicserver import renderjson
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

if not debug:
    def report_report_attribute_access(cls):
        return cls
else:
    def report_attribute_access(cls):
        ''' Class decorator to trace attribute read access; to debug routing.
        '''
        def attribute_lookup_wrapper(instance, attrname):
            try:
                try:
                    value = cls.__getattribute__(instance, attrname)    # default
                except AttributeError:
                    value = cls.__getattr__(instance, attrname)         # fallback
            except:
                outcome = '?'
                raise
            else:
                outcome = '=> {0}'.format(value)
                return value
            finally:
                if not attrname.startswith('__'):
                    call = '{0}.{1}'.format(instance, attrname)
                    print(call, outcome)

        def short_repr(instance):
            short_id = hex(id(instance))[-4:]
            return '{0}:{1}'.format(instance.__class__.__name__, short_id)

        subclass = type(cls.__name__, (cls,), {
            '__getattribute__': attribute_lookup_wrapper,
            '__repr__': short_repr,
        })
        return subclass


def _get_controller(name):
    qualname = __qualify_module(name)
    try:
        return sys.modules[qualname]
    except KeyError:
        try:
            return __import_module(qualname)
        except ImportError as e:
            print(e)
            raise LookupError(name)


def __import_module(qualname):
    __import__(qualname)
    return sys.modules[qualname]


def __qualify_module(name):
    return '.'.join((__package__, name))


@report_attribute_access
class RESTResource(object):
    exposed = True

    # CherryPy auto-responds with 405 status for undefined HTTP methods

    def parsepath(self, path_elements, min_length=0):
        padding = (None,) * (min_length - len(path_elements))
        return tuple(path_elements) + padding


class Media(RESTResource):
    def GET(self, *vpath, **params):
        pass


class Playlists(RESTResource):
    def GET(self, *vpath, **params):
        plformat = params.get('format', 'json')
        username, playlistid = self.parsepath(vpath, 2)
        if username:
            if playlistid:
                # get specific playlist
                pass
            else:
                # get playlists by user
                pass
        else:
            # get all playlists
            pass


class Users(RESTResource):
    def GET(self, *vpath, **params):
        username = self.parsepath(vpath, 1)
        if username:
            # get user info
            pass
        else:
            # get user list
            pass


class Sessions(RESTResource):
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


@report_attribute_access
@service.user(model='cherrymodel', playlistdb='playlist',
              useroptions='useroptions', userdb='users')
class RESTInterfaceV1(object):

    exposed = True

    def GET(self, *subpath, **params):
        ''' For GET to work without a subpath, i.e. for index requests,
            there must be no `default` or `index` methods in the handler,
            since CherryPy tries these before falling back to the member
            whose name matches the HTTP request method.
        '''
        return '{0} {1} {2}'.format('RESTInterfaceV1().GET', subpath, params)

    def __getattr__(self, name):
        ''' When routing subpaths, CherryPy first looks at attributes. GET
            is the fallback, *if* it allows enough positional arguments.

            .. warning::
                This method instantiates a new resource controller for each
                request. This is bad form and not intended for production.
        '''
        if name.startswith('_'):
            raise AttributeError(name)
        try:
            return _get_controller(name)
        except LookupError:
            raise AttributeError(name)

    def __init__(self, config):
        self.config = config

        template_main = 'res/main.html'
        template_login = 'res/login.html'
        template_firstrun = 'res/firstrun.html'

        self.mainpage = readRes(template_main)
        self.loginpage = readRes(template_login)
        self.firstrunpage = readRes(template_firstrun)

        # rest resource names
        self.media = Media()
        self.playlists = Playlists()
        self.media = Media()

    def issecure(self, url):
        return parse.urlparse(url).scheme == 'https'

    def getBaseUrl(self, redirect_unencrypted=False):
        ipAndPort = parse.urlparse(cherrypy.url()).netloc
        is_secure_connection = self.issecure(cherrypy.url())
        ssl_enabled = cherry.config['server.ssl_enabled']
        if ssl_enabled and not is_secure_connection:
            log.d('Not secure, redirecting...')
            ip = ipAndPort[:ipAndPort.rindex(':')]
            url = 'https://' + ip + ':' + str(cherry.config['server.ssl_port'])
            if redirect_unencrypted:
                raise cherrypy.HTTPRedirect(url, 302)
        else:
            url = 'http://' + ipAndPort
        return url

    def index(self, *args, **kwargs):
        self.getBaseUrl(redirect_unencrypted=True)
        firstrun = 0 == self.userdb.getUserCount()
        if debug:
            #reload pages everytime in debig mode
            self.mainpage = readRes('res/main.html')
            self.loginpage = readRes('res/login.html')
            self.firstrunpage = readRes('res/firstrun.html')

        if cherrypy.session['username']:
            pass
        if 'login' in kwargs:
            username = kwargs.get('username', '')
            password = kwargs.get('password', '')
            login_action = kwargs.get('login', '')
            if login_action == 'login':
                self.session_auth(username, password)
                if cherrypy.session['username']:
                    username = cherrypy.session['username']
                    log.i('user %s just logged in.' % username)
            elif login_action == 'create admin user':
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
        try:
            sessionUsername = cherrypy.session.get('username', None)
            sessionUserId = cherrypy.session.get('userid', -1)
            nameById = self.userdb.getNameById(sessionUserId)
        except (UnicodeDecodeError, ValueError) as e:
            # workaround for python2/python3 jump, filed bug in cherrypy
            # https://bitbucket.org/cherrypy/cherrypy/issue/1216/sessions-python2-3-compability-unsupported
            log.w('''
Dropping all sessions! Try not to change between python 2 and 3,
everybody has to relogin now.''')
            cherrypy.session.delete()
            sessionUsername = None
        if not sessionUsername:
            return self.autoLoginIfPossible()
        elif sessionUsername != nameById:
            self.api_logout(value=None)
            return False
        return True

    def autoLoginIfPossible(self):
        is_loopback = cherrypy.request.remote.ip in ('127.0.0.1', '::1')
        if is_loopback and cherry.config['server.localhost_auto_login']:
            cherrypy.session['username'] = self.userdb.getNameById(1)
            cherrypy.session['userid'] = 1
            cherrypy.session['admin'] = True
            return True
        return False

    def session_auth(self, username, password):
        user = self.userdb.auth(username, password)
        allow_remote = cherry.config['server.permit_remote_admin_login']
        is_loopback = cherrypy.request.remote.ip in ('127.0.0.1', '::1')
        if not is_loopback and user.isadmin and not allow_remote:
            log.i('Rejected remote admin login from user: %s' % user.name)
            user = userdb.User.nobody()
        cherrypy.session['username'] = user.name
        cherrypy.session['userid'] = user.uid
        cherrypy.session['admin'] = user.isadmin

    def getUserId(self):
        try:
            return cherrypy.session['userid']
        except KeyError:
            cherrypy.lib.sessions.expire()
            cherrypy.HTTPRedirect(cherrypy.url(), 302)
            return ''

    def trans(self, *args):
        if not self.isAuthorized():
            raise cherrypy.HTTPRedirect(self.getBaseUrl(), 302)
        cherrypy.session.release_lock()
        if cherry.config['media.transcode'] and len(args):
            newformat = args[-1][4:]  # get.format
            path = os.path.sep.join(args[:-1])
            """ugly workaround for #273, should be handled somewhere in
            cherrypy, but don't know where...
            """
            if sys.version_info < (3, 0):
                path = path
            else:
                path = codecs.decode(codecs.encode(path, 'latin1'), 'utf-8')
            fullpath = os.path.join(cherry.config['media.basedir'], path)
            transcoder = audiotranscode.AudioTranscode()
            mimetype = transcoder.mimeType(newformat)
            cherrypy.response.headers["Content-Type"] = mimetype
            return transcoder.transcodeStream(fullpath, newformat)
    trans.exposed = True
    trans._cp_config = {'response.stream': True}

    def api(self, *args, **kwargs):
        """calls the appropriate handler from the handlers
        dict, if available. handlers having noauth set to
        true do not need authentification to work.
        """
        #check action
        action = args[0] if args else ''
        if not action in self.handlers:
            return "Error: no such action."
        #authorize if not explicitly deactivated
        handler = self.handlers[action]
        needsAuth = not ('noauth' in dir(handler) and handler.noauth)
        if needsAuth and not self.isAuthorized():
            raise cherrypy.HTTPError(401, 'Unauthorized')
        #parse value (is list of arguments, but if the list has only
        #one element, this element is directly passed to the handler)
        value = kwargs.get('value', '')
        if not value and len(args) > 1:
            value = list(map(unquote, args[1:len(args)]))
            if len(value) == 1:
                value = value[0]
        return handler(value)
    api.exposed = True

    def api_customcss(self, value):
        cherrypy.response.headers["Content-Type"] = 'text/css'
        opts = self.useroptions.forUser(self.getUserId()).getOptions()
        primary_color = opts.custom_theme.primary_color.value
        primary_dark = self.brightness(primary_color, -40)
        primary_bright = self.brightness(primary_color, 70)
        style = """
            .active{{
                background-color: {primary} !important;
            }}
            .button{{
                background-color: {primary} !important;
                border-color: {primary_bright} {primary_dark}
                              {primary_dark} {primary_bright} !important;
            }}
            .button:hover{{
                background-color: {primary_dark} !important;
                border-color:{primary_dark} {primary_bright}
                             {primary_bright} {primary_dark} !important;
            }}
            .bigbutton{{
                background-color: {primary} !important;
                border-color: {primary_bright} {primary_dark}
                              {primary_dark} {primary_bright} !important;
            }}
            .bigbutton:hover{{
                background-color: {primary_dark} !important;
                border-color: {primary_dark} {primary_bright}
                              {primary_bright} {primary_dark} !important;
            }}
            .smalltab{{
                background-color: {primary} !important;
            }}
        """.format(primary=opts.custom_theme.primary_color.value,
                   primary_dark=primary_dark,
                   primary_bright=primary_bright,
                   #background = opts.custom_theme.background_color.value,
                   #text = invert(opts.custom_theme.background_color.value)
                   )
        if opts.custom_theme.white_on_black.bool:
            style += """
            html{
                background-color: #000000 !important;
            }
            #mediaplayer{
                background-color: #000000 !important;
            }
            .black{
                color: #ffffff !important;
            }
            .listdir, .compactlistdir, .fileinlist{
                background-color: #222222;
                color: #ffffff;
            }
            li.fileinlist {
                background-color: #424242 !important;
            }
            li.fileinlist a {
                color: #AFAFAF !important;
            }
            .compactlistdir {
                background-color: #005500 !important;
            }
            div.jp-playlist a {
                color: #FFFFFF !important;
            }
            div.jp-title, div.jp-playlist {
                background-color: #444444 !important;
            }
            #playlistCommands {
                background-color: #444444;
            }
            """
        return style

    def api_download(self, filelist):
        #TODO: make sure file are not outside of basedir
        size_limit = cherry.config['media.maximum_download_size']
        active_download = cherrypy.session.get('active_download', False)
        if not active_download:
            if self.model.file_size_within_limit(filelist, maximum_download_size):
                cherrypy.session['active_download'] = True
                cherrypy.session.release_lock()
                cherrypy.response.headers["Content-Type"] = 'application/zip'
                cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="dl.zip"'
                chunk = self.model.compress(filelist)
                while not chunk is None:
                    yield chunk
                    chunk = self.model.compress(filelist)
    api_download._cp_config = {'response.stream': True}


    def invert(self, htmlcolor):
        r, g, b = self.html2rgb(htmlcolor)
        return '#'+self.rgb2hex(255-r, 255-b, 255-b)

    def brightness(self, htmlcolor, brightness):
        r, g, b = self.html2rgb(htmlcolor)
        r = min(max(r+brightness, 0), 255)
        g = min(max(g+brightness, 0), 255)
        b = min(max(b+brightness, 0), 255)
        return '#'+self.rgb2hex(r, g, b)

    def html2rgb(self, htmlcolor):
        r = int(htmlcolor[1:3], 16)
        g = int(htmlcolor[3:5], 16)
        b = int(htmlcolor[5:7], 16)
        return r, g, b

    def rgb2hex(self, r, g, b):
        r = hex(r)[2:].zfill(2)
        g = hex(g)[2:].zfill(2)
        b = hex(b)[2:].zfill(2)
        return r+g+b

    def api_getuseroptions(self, value):
        uo = self.useroptions.forUser(self.getUserId())
        uco = uo.getChangableOptions()
        return json.dumps(uco)

    def api_heartbeat(self, value):
        uo = self.useroptions.forUser(self.getUserId())
        uo.setOption('last_time_online', int(time.time()))

    def api_setuseroption(self, value):
        params = json.loads(value)
        uo = self.useroptions.forUser(self.getUserId())
        uo.setOption(params["optionkey"], params["optionval"])
        return "success"

    def api_fetchalbumart(self, value):
        cherrypy.session.release_lock()
        params = json.loads(value)
        directory = params['directory']

        #try getting a cached album art image
        b64imgpath = albumArtFilePath(directory)
        img_data = self.albumartcache_load(b64imgpath)
        if img_data:
            cherrypy.response.headers["Content-Length"] = len(img_data)
            return img_data

        #try getting album art inside local folder
        fetcher = albumartfetcher.AlbumArtFetcher()
        localpath = os.path.join(cherry.config['media.basedir'], directory)
        header, data, resized = fetcher.fetchLocal(localpath)

        if header:
            if resized:
                #cache resized image for next time
                self.albumartcache_save(b64imgpath, data)
            cherrypy.response.headers.update(header)
            return data
        elif cherry.config['media.fetch_album_art']:
            #fetch album art from online source
            album = os.path.basename(directory)
            artist = os.path.basename(os.path.dirname(directory))
            keywords = artist+' '+album
            log.i("Fetching album art for keywords '%s'" % keywords)
            header, data = fetcher.fetch(keywords)
            if header:
                cherrypy.response.headers.update(header)
                self.albumartcache_save(b64imgpath, data)
                return data
        cherrypy.HTTPRedirect("/res/img/folder.png", 302)
    api_fetchalbumart.noauth = True

    def albumartcache_load(self, imgb64path):
        if os.path.exists(imgb64path):
            with open(imgb64path, 'rb') as f:
                return f.read()

    def albumartcache_save(self, path, data):
        with open(path, 'wb') as f:
            f.write(data)

    def api_compactlistdir(self, value):
        params = json.loads(value)
        dirtorender = params['directory']
        files_to_list = self.model.listdir(dirtorender, params['filter'])
        return self.jsonrenderer.render(files_to_list)

    def api_listdir(self, value):
        if value:
            params = json.loads(value)
            dirtorender = params['directory']
        else:
            dirtorender = ''
        return self.jsonrenderer.render(self.model.listdir(dirtorender))

    def api_search(self, value):
        if not value.strip():
            jsonresults = '[]'
        else:
            with Performance('processing whole search request'):
                searchresults = self.model.search(value.strip())
                with Performance('rendering search results as json'):
                    jsonresults = self.jsonrenderer.render(searchresults)
        return jsonresults

    def api_rememberplaylist(self, value):
        cherrypy.session['playlist'] = value

    def api_saveplaylist(self, value):
        pl = json.loads(value)
        userid = self.getUserId()
        public = 1 if pl['public'] else 0
        playlist = pl['playlist']
        title = pl['playlistname']
        overwrite = pl.get('overwrite', False)
        res, playlistid = self.playlistdb.savePlaylist(userid=userid,
                                                       public=public,
                                                       playlist=playlist,
                                                       playlisttitle=title,
                                                       overwrite=overwrite)
        if res == "success":
            return json.dumps({'playlistid': playlistid})
        else:
            raise cherrypy.HTTPError(400, res)

    def api_deleteplaylist(self, value):
        res = self.playlistdb.deletePlaylist(value,
                                             self.getUserId(),
                                             override_owner=False)
        if res == "success":
            return res
        else:
            # not the ideal status code but we don't know the actual
            # cause without parsing res
            raise cherrypy.HTTPError(400, res)

    def api_loadplaylist(self, value):
        return self.jsonrenderer.render(self.playlistdb.loadPlaylist(
                                        playlistid=value,
                                        userid=self.getUserId()
                                        ))

    def api_changeplaylist(self, value):
        params = json.loads(value)
        is_public = params['attribute'] == 'public'
        is_valid = type(params['value']) == bool and type(params['plid']) == int
        if is_public and is_valid:
            return self.playlistdb.setPublic(userid=self.getUserId(),
                                             plid=params['plid'],
                                             value=params['value'])

    def api_getmotd(self, value):
        return self.model.motd()

    def api_restoreplaylist(self, value):
        session_playlist = cherrypy.session.get('playlist', '[]')
        return session_playlist

    def api_getplayables(self, value):
        """DEPRECATED"""
        return json.dumps(cherry.config['media.playable'])

    def api_getuserlist(self, value):
        if cherrypy.session['admin']:
            userlist = self.userdb.getUserList()
            for user in userlist:
                if user['id'] == cherrypy.session['userid']:
                    user['deletable'] = False
                user_options = self.useroptions.forUser(user['id'])
                t = user_options.getOptionValue('last_time_online')
                user['last_time_online'] = t
            return json.dumps({'time': int(time.time()),
                               'userlist': userlist})
        else:
            return json.dumps({'time': 0, 'userlist': []})

    def api_adduser(self, value):
        if cherrypy.session['admin']:
            new = json.loads(value)
            return self.userdb.addUser(new['username'],
                                       new['password'],
                                       new['isadmin'])
        else:
            return "You didn't think that would work, did you?"

    def api_userchangepassword(self, value):
        params = json.loads(value)
        isself = not 'userid' in params
        if isself:
            params['username'] = cherrypy.session['username']
            authed_user = self.userdb.auth(params['username'],
                                           params['oldpassword'])
            is_authenticated = userdb.User.nobody() != authed_user
            if not is_authenticated:
                raise cherrypy.HTTPError(403, "Forbidden")
        if isself or cherrypy.session['admin']:
            return self.userdb.changePassword(params['username'],
                                              params['newpassword'])
        else:
            raise cherrypy.HTTPError(403, "Forbidden")

    def api_userdelete(self, value):
        params = json.loads(value)
        is_self = cherrypy.session['userid'] == params['userid']
        if cherrypy.session['admin'] and not is_self:
            deleted = self.userdb.deleteUser(params['userid'])
            return 'success' if deleted else 'failed'
        else:
            return "You didn't think that would work, did you?"

    def api_showplaylists(self, value):
        playlists = self.playlistdb.showPlaylists(self.getUserId())
        #translate userids to usernames:
        for pl in playlists:
            pl['username'] = self.userdb.getNameById(pl['userid'])
        return json.dumps(playlists)

    def api_logout(self, value):
        cherrypy.lib.sessions.expire()
    api_logout.no_auth = True

    def api_downloadpls(self, value):
        dlval = json.loads(value)
        pls = self.playlistdb.createPLS(dlval['plid'],
                                        self.getUserId(),
                                        dlval['addr'])
        name = self.playlistdb.getName(value, self.getUserId())
        if pls and name:
            return self.serve_string_as_file(pls, name+'.pls')

    def api_downloadm3u(self, value):
        dlval = json.loads(value)
        pls = self.playlistdb.createM3U(dlval['plid'],
                                        self.getUserId(),
                                        dlval['addr'])
        name = self.playlistdb.getName(value, self.getUserId())
        if pls and name:
            return self.serve_string_as_file(pls, name+'.m3u')

    def api_getsonginfo(self, value):
        basedir = cherry.config['media.basedir']
        #TODO yet another dirty hack. removing the /serve thing is a mess.
        path = unquote(value)
        if path.startswith('/serve/'):
            path = path[7:]
        elif path.startswith('serve/'):
            path = path[6:]
        abspath = os.path.join(basedir, path)
        return json.dumps(metainfo.getSongInfo(abspath).dict())

    def api_getencoders(self, value):
        return json.dumps(audiotranscode.getEncoders())

    def api_getdecoders(self, value):
        return json.dumps(audiotranscode.getDecoders())

    def api_transcodingenabled(self, value):
        return json.dumps(cherry.config['media.transcode'])

    def api_updatedb(self, value):
        self.model.updateLibrary()
        return 'success'

    def api_getconfiguration(self, value):
        clientconfigkeys = {
            'transcodingenabled': cherry.config['media.transcode'],
            'fetchalbumart': cherry.config['media.fetch_album_art'],
            'isadmin': cherrypy.session['admin'],
            'username': cherrypy.session['username'],
        }
        if cherry.config['media.transcode']:
            decoders = self.model.transcoder.availableDecoderFormats()
            clientconfigkeys['getdecoders'] = decoders
            encoders = self.model.transcoder.availableEncoderFormats()
            clientconfigkeys['getencoders'] = encoders
        else:
            clientconfigkeys['getdecoders'] = []
            clientconfigkeys['getencoders'] = []
        return json.dumps(clientconfigkeys)

    def serve_string_as_file(self, string, filename):
        content_disposition = 'attachment; filename="'+filename+'"'
        cherrypy.response.headers["Content-Type"] = "application/x-download"
        cherrypy.response.headers["Content-Disposition"] = content_disposition
        return codecs.encode(string, "UTF-8")
