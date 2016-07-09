#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
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

import os  # shouldn't have to list any folder in the future!
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
from tinytag import TinyTag

from cherrymusicserver import userdb
from cherrymusicserver import log
from cherrymusicserver import albumartfetcher
from cherrymusicserver import service
from cherrymusicserver.pathprovider import readRes
from cherrymusicserver.pathprovider import albumArtFilePath
import cherrymusicserver as cherry
import cherrymusicserver.metainfo as metainfo
from cherrymusicserver.util import Performance, MemoryZipFile

from cherrymusicserver.ext import zipstream
import time

debug = True


@service.user(model='cherrymodel', playlistdb='playlist',
              useroptions='useroptions', userdb='users')
class HTTPHandler(object):
    def __init__(self, config):
        self.config = config

        template_main = 'res/dist/main.html'
        template_login = 'res/login.html'
        template_firstrun = 'res/firstrun.html'

        self.mainpage = readRes(template_main)
        self.loginpage = readRes(template_login)
        self.firstrunpage = readRes(template_firstrun)

        self.handlers = {
            'search': self.api_search,
            'rememberplaylist': self.api_rememberplaylist,
            'saveplaylist': self.api_saveplaylist,
            'loadplaylist': self.api_loadplaylist,
            'generaterandomplaylist': self.api_generaterandomplaylist,
            'deleteplaylist': self.api_deleteplaylist,
            'getmotd': self.api_getmotd,
            'restoreplaylist': self.api_restoreplaylist,
            'getplayables': self.api_getplayables,
            'getuserlist': self.api_getuserlist,
            'adduser': self.api_adduser,
            'userdelete': self.api_userdelete,
            'userchangepassword': self.api_userchangepassword,
            'showplaylists': self.api_showplaylists,
            'logout': self.api_logout,
            'downloadpls': self.api_downloadpls,
            'downloadm3u': self.api_downloadm3u,
            'getsonginfo': self.api_getsonginfo,
            'getencoders': self.api_getencoders,
            'getdecoders': self.api_getdecoders,
            'transcodingenabled': self.api_transcodingenabled,
            'updatedb': self.api_updatedb,
            'getconfiguration': self.api_getconfiguration,
            'compactlistdir': self.api_compactlistdir,
            'listdir': self.api_listdir,
            'fetchalbumart': self.api_fetchalbumart,
            'fetchalbumarturls': self.api_fetchalbumarturls,
            'albumart_set': self.api_albumart_set,
            'heartbeat': self.api_heartbeat,
            'getuseroptions': self.api_getuseroptions,
            'setuseroption': self.api_setuseroption,
            'changeplaylist': self.api_changeplaylist,
            'downloadcheck': self.api_downloadcheck,
            'setuseroptionfor': self.api_setuseroptionfor,
        }

    def issecure(self, url):
        return parse.urlparse(url).scheme == 'https'

    def getBaseUrl(self, redirect_unencrypted=False):
        ipAndPort = parse.urlparse(cherrypy.url()).netloc
        is_secure_connection = self.issecure(cherrypy.url())
        ssl_enabled = cherry.config['server.ssl_enabled']
        if ssl_enabled and not is_secure_connection:
            log.d(_('Not secure, redirecting...'))
            try:
                ip = ipAndPort[:ipAndPort.rindex(':')]
            except ValueError:
                ip = ipAndPort  # when using port 80: port is not in ipAndPort
            url = 'https://' + ip + ':' + str(cherry.config['server.ssl_port'])
            if redirect_unencrypted:
                raise cherrypy.HTTPRedirect(url, 302)
        else:
            url = 'http://' + ipAndPort
        return url

    def index(self, *args, **kwargs):
        self.getBaseUrl(redirect_unencrypted=True)
        firstrun = 0 == self.userdb.getUserCount()
        show_page = self.mainpage #generated main.html from devel.html
        if 'devel' in kwargs:
            #reload pages everytime in devel mode
            show_page = readRes('res/devel.html')
            self.loginpage = readRes('res/login.html')
            self.firstrunpage = readRes('res/firstrun.html')
        if 'login' in kwargs:
            username = kwargs.get('username', '')
            password = kwargs.get('password', '')
            login_action = kwargs.get('login', '')
            if login_action == 'login':
                self.session_auth(username, password)
                if cherrypy.session['username']:
                    username = cherrypy.session['username']
                    log.i(_('user {name} just logged in.').format(name=username))
            elif login_action == 'create admin user':
                if firstrun:
                    if username.strip() and password.strip():
                        self.userdb.addUser(username, password, True)
                        self.session_auth(username, password)
                        return show_page
                else:
                    return "No, you can't."
        if firstrun:
            return self.firstrunpage
        else:
            if self.isAuthorized():
                return show_page
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
            log.w(_('''
            Dropping all sessions! Try not to change between python 2 and 3,
            everybody has to relogin now.'''))
            cherrypy.session.delete()
            sessionUsername = None
        if sessionUsername is None:
            if self.autoLoginActive():
                cherrypy.session['username'] = self.userdb.getNameById(1)
                cherrypy.session['userid'] = 1
                cherrypy.session['admin'] = True
                return True
            else:
                return False
        elif sessionUsername != nameById:
            self.api_logout(value=None)
            return False
        return True

    def autoLoginActive(self):
        is_loopback = cherrypy.request.remote.ip in ('127.0.0.1', '::1')
        if is_loopback and cherry.config['server.localhost_auto_login']:
            return True
        return False

    def session_auth(self, username, password):
        user = self.userdb.auth(username, password)
        allow_remote = cherry.config['server.permit_remote_admin_login']
        is_loopback = cherrypy.request.remote.ip in ('127.0.0.1', '::1')
        if not is_loopback and user.isadmin and not allow_remote:
            log.i(_('Rejected remote admin login from user: {name}').format(name=user.name))
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

    def trans(self, newformat, *path, **params):
        ''' Transcodes the track given as ``path`` into ``newformat``.

            Streams the response of the corresponding
            ``audiotranscode.AudioTranscode().transcodeStream()`` call.

            params:
                bitrate: int for kbps. None or < 1 for default
        '''
        if not self.isAuthorized():
            raise cherrypy.HTTPRedirect(self.getBaseUrl(), 302)
        cherrypy.session.release_lock()
        if cherry.config['media.transcode'] and path:

            # bitrate
            bitrate = params.pop('bitrate', None) or None  # catch empty strings
            if bitrate:
                try:
                    bitrate = max(0, int(bitrate)) or None  # None if < 1
                except (TypeError, ValueError):
                    raise cherrypy.HTTPError(400, "Bad query: "
                        "bitrate ({0!r}) must be an integer".format(str(bitrate)))

            # path
            path = os.path.sep.join(path)
            if sys.version_info < (3, 0):       # workaround for #327 (cherrypy issue)
                path = path.decode('utf-8')     # make it work with non-ascii
            else:
                path = codecs.decode(codecs.encode(path, 'latin1'), 'utf-8')
            fullpath = os.path.join(cherry.config['media.basedir'], path)

            starttime = int(params.pop('starttime', 0))

            transcoder = audiotranscode.AudioTranscode()
            mimetype = audiotranscode.mime_type(newformat)
            cherrypy.response.headers["Content-Type"] = mimetype
            try:
                return transcoder.transcode_stream(fullpath, newformat,
                            bitrate=bitrate, starttime=starttime)
            except (audiotranscode.TranscodeError, IOError) as e:
                raise cherrypy.HTTPError(404, e.value)
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
            return "Error: no such action. '%s'" % action
        #authorize if not explicitly deactivated
        handler = self.handlers[action]
        needsAuth = not ('noauth' in dir(handler) and handler.noauth)
        if needsAuth and not self.isAuthorized():
            raise cherrypy.HTTPError(401, 'Unauthorized')
        handler_args = {}
        if 'data' in kwargs:
            handler_args = json.loads(kwargs['data'])
        is_binary = ('binary' in dir(handler) and handler.binary)
        if is_binary:
            return handler(**handler_args)
        else:
            return json.dumps({'data': handler(**handler_args)})

    api.exposed = True

    def download_check_files(self, filelist):
        # only admins and allowed users may download
        if not cherrypy.session['admin']:
            uo = self.useroptions.forUser(self.getUserId())
            if not uo.getOptionValue('media.may_download'):
                return 'not_permitted'
        # make sure nobody tries to escape from basedir
        for f in filelist:
            # don't allow to traverse up in the file system
            if '/../' in f or f.startswith('../'):
                return 'invalid_file'
            # CVE-2015-8309: do not allow absolute file paths
            if os.path.isabs(f):
                return 'invalid_file'
        # make sure all files are smaller than maximum download size
        size_limit = cherry.config['media.maximum_download_size']
        try:
            if self.model.file_size_within_limit(filelist, size_limit):
                return 'ok'
            else:
                return 'too_big'
        except OSError as e:        # use OSError for python2 compatibility
            return str(e)

    def api_downloadcheck(self, filelist):
        status = self.download_check_files(filelist)
        if status == 'not_permitted':
            return """You are not allowed to download files."""
        elif status == 'invalid_file':
            return "Error: invalid filename found in {list}".format(list=filelist)
        elif status == 'too_big':
            size_limit = cherry.config['media.maximum_download_size']
            return """Can't download: Playlist is bigger than {maxsize} mB.
                        The server administrator can change this configuration.
                        """.format(maxsize=size_limit/1024/1024)
        elif status == 'ok':
            return status
        else:
            message = "Error status check for download: {status!r}".format(status=status)
            log.e(message)
            return message

    def download(self, value):
        if not self.isAuthorized():
            raise cherrypy.HTTPError(401, 'Unauthorized')
        filelist = [filepath for filepath in json.loads(unquote(value))]
        dlstatus = self.download_check_files(filelist)
        if dlstatus == 'ok':
            _save_and_release_session()
            zipmime = 'application/x-zip-compressed'
            cherrypy.response.headers["Content-Type"] = zipmime
            zipname = 'attachment; filename="music.zip"'
            cherrypy.response.headers['Content-Disposition'] = zipname
            basedir = cherry.config['media.basedir']
            fullpath_filelist = [os.path.join(basedir, f) for f in filelist]
            return zipstream.ZipStream(fullpath_filelist)
        else:
            return dlstatus
    download.exposed = True
    download._cp_config = {'response.stream': True}

    def api_getuseroptions(self):
        uo = self.useroptions.forUser(self.getUserId())
        uco = uo.getChangableOptions()
        if cherrypy.session['admin']:
            uco['media'].update({'may_download': True})
        else:
            uco['media'].update({'may_download': uo.getOptionValue('media.may_download')})
        return uco

    def api_heartbeat(self):
        uo = self.useroptions.forUser(self.getUserId())
        uo.setOption('last_time_online', int(time.time()))

    def api_setuseroption(self, optionkey, optionval):
        uo = self.useroptions.forUser(self.getUserId())
        uo.setOption(optionkey, optionval)
        return "success"

    def api_setuseroptionfor(self, userid, optionkey, optionval):
        if cherrypy.session['admin']:
            uo = self.useroptions.forUser(userid)
            uo.setOption(optionkey, optionval)
            return "success"
        else:
            return "error: not permitted. Only admins can change other users options"

    def api_fetchalbumarturls(self, searchterm):
        if not cherrypy.session['admin']:
            raise cherrypy.HTTPError(401, 'Unauthorized')
        _save_and_release_session()
        fetcher = albumartfetcher.AlbumArtFetcher()
        imgurls = fetcher.fetchurls(searchterm)
        # show no more than 10 images
        return imgurls[:min(len(imgurls), 10)]

    def api_albumart_set(self, directory, imageurl):
        if not cherrypy.session['admin']:
            raise cherrypy.HTTPError(401, 'Unauthorized')
        b64imgpath = albumArtFilePath(directory)
        fetcher = albumartfetcher.AlbumArtFetcher()
        data, header = fetcher.retrieveData(imageurl)
        self.albumartcache_save(b64imgpath, data)

    def api_fetchalbumart(self, directory):
        _save_and_release_session()
        default_folder_image = "../res/img/folder.png"

        log.i('Fetching album art for: %s' % directory)
        filepath = os.path.join(cherry.config['media.basedir'], directory)

        if os.path.isfile(filepath):
            # if the given path is a file, try to get the image from ID3
            tag = TinyTag.get(filepath, image=True)
            image_data = tag.get_image()
            if image_data:
                log.d('Image found in tag.')
                header = {'Content-Type': 'image/jpg', 'Content-Length': len(image_data)}
                cherrypy.response.headers.update(header)
                return image_data
            else:
                # if the file does not contain an image, display the image of the
                # parent directory
                directory = os.path.dirname(directory)

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
            try:
                foldername = os.path.basename(directory)
                keywords = foldername
                log.i(_("Fetching album art for keywords {keywords!r}").format(keywords=keywords))
                header, data = fetcher.fetch(keywords)
                if header:
                    cherrypy.response.headers.update(header)
                    self.albumartcache_save(b64imgpath, data)
                    return data
                else:
                    # albumart fetcher failed, so we serve a standard image
                    raise cherrypy.HTTPRedirect(default_folder_image, 302)
            except:
                # albumart fetcher threw exception, so we serve a standard image
                raise cherrypy.HTTPRedirect(default_folder_image, 302)
        else:
            # no local album art found, online fetching deactivated, show default
            raise cherrypy.HTTPRedirect(default_folder_image, 302)
    api_fetchalbumart.noauth = True
    api_fetchalbumart.binary = True

    def albumartcache_load(self, imgb64path):
        if os.path.exists(imgb64path):
            with open(imgb64path, 'rb') as f:
                return f.read()

    def albumartcache_save(self, path, data):
        with open(path, 'wb') as f:
            f.write(data)

    def api_compactlistdir(self, directory, filterstr=None):
        try:
            files_to_list = self.model.listdir(directory, filterstr)
        except ValueError:
            raise cherrypy.HTTPError(400, 'Bad Request')
        return [entry.to_dict() for entry in files_to_list]

    def api_listdir(self, directory):
        try:
            return [entry.to_dict() for entry in self.model.listdir(directory)]
        except ValueError:
            raise cherrypy.HTTPError(400, 'Bad Request')

    def api_search(self, searchstring):
        if not searchstring.strip():
            jsonresults = '[]'
        else:
            with Performance(_('processing whole search request')):
                searchresults = self.model.search(searchstring.strip())
                with Performance(_('rendering search results as json')):
                    jsonresults = [entry.to_dict() for entry in searchresults]
        return jsonresults

    def api_rememberplaylist(self, playlist):
        cherrypy.session['playlist'] = playlist

    def api_saveplaylist(self, playlist, public, playlistname, overwrite=False):
        res = self.playlistdb.savePlaylist(
            userid=self.getUserId(),
            public=1 if public else 0,
            playlist=playlist,
            playlisttitle=playlistname,
            overwrite=overwrite)
        if res == "success":
            return res
        else:
            raise cherrypy.HTTPError(400, res)

    def api_deleteplaylist(self, playlistid):
        res = self.playlistdb.deletePlaylist(playlistid,
                                             self.getUserId(),
                                             override_owner=False)
        if res == "success":
            return res
        else:
            # not the ideal status code but we don't know the actual
            # cause without parsing res
            raise cherrypy.HTTPError(400, res)

    def api_loadplaylist(self, playlistid):
        return [entry.to_dict() for entry in self.playlistdb.loadPlaylist(
                                        playlistid=playlistid,
                                        userid=self.getUserId()
                                        )]

    def api_generaterandomplaylist(self):
        return [entry.to_dict() for entry in self.model.randomMusicEntries(50)]

    def api_changeplaylist(self, plid, attribute, value):
        if attribute == 'public':
            is_valid = type(value) == bool and type(plid) == int
            if is_valid:
                return self.playlistdb.setPublic(userid=self.getUserId(),
                                                 plid=plid,
                                                 public=value)

    def api_getmotd(self):
        if cherrypy.session['admin'] and cherry.config['general.update_notification']:
            _save_and_release_session()
            new_versions = self.model.check_for_updates()
            if new_versions:
                newest_version = new_versions[0]['version']
                features = []
                fixes = []
                for version in new_versions:
                    for update in version['features']:
                        if update.startswith('FEATURE:'):
                            features.append(update[len('FEATURE:'):])
                        elif update.startswith('FIX:'):
                            fixes.append(update[len('FIX:'):])
                        elif update.startswith('FIXED:'):
                            fixes.append(update[len('FIXED:'):])
                retdata = {'type': 'update', 'data': {}}
                retdata['data']['version'] = newest_version
                retdata['data']['features'] = features
                retdata['data']['fixes'] = fixes
                return retdata
        return {'type': 'wisdom', 'data': self.model.motd()}

    def api_restoreplaylist(self):
        session_playlist = cherrypy.session.get('playlist', [])
        return session_playlist

    def api_getplayables(self):
        """DEPRECATED"""
        return json.dumps(cherry.config['media.playable'])

    def api_getuserlist(self):
        if cherrypy.session['admin']:
            userlist = self.userdb.getUserList()
            for user in userlist:
                if user['id'] == cherrypy.session['userid']:
                    user['deletable'] = False
                user_options = self.useroptions.forUser(user['id'])
                t = user_options.getOptionValue('last_time_online')
                may_download = user_options.getOptionValue('media.may_download')
                user['last_time_online'] = t
                user['may_download'] = may_download
            sortfunc = lambda user: user['last_time_online']
            userlist = sorted(userlist, key=sortfunc, reverse=True)
            return json.dumps({'time': int(time.time()),
                               'userlist': userlist})
        else:
            return json.dumps({'time': 0, 'userlist': []})

    def api_adduser(self, username, password, isadmin):
        if cherrypy.session['admin']:
            if self.userdb.addUser(username, password, isadmin):
                return 'added new user: %s' % username
            else:
                return 'error, cannot add new user!' % username
        else:
            return "You didn't think that would work, did you?"

    def api_userchangepassword(self, oldpassword, newpassword, username=''):
        isself = username == ''
        if isself:
            username = cherrypy.session['username']
            authed_user = self.userdb.auth(username, oldpassword)
            is_authenticated = userdb.User.nobody() != authed_user
            if not is_authenticated:
                raise cherrypy.HTTPError(403, "Forbidden")
        if isself or cherrypy.session['admin']:
            return self.userdb.changePassword(username, newpassword)
        else:
            raise cherrypy.HTTPError(403, "Forbidden")

    def api_userdelete(self, userid):
        is_self = cherrypy.session['userid'] == userid
        if cherrypy.session['admin'] and not is_self:
            deleted = self.userdb.deleteUser(userid)
            return 'success' if deleted else 'failed'
        else:
            return "You didn't think that would work, did you?"

    def api_showplaylists(self, sortby="created", filterby=''):
        playlists = self.playlistdb.showPlaylists(self.getUserId(), filterby)
        curr_time = int(time.time())
        is_reverse = False
        #translate userids to usernames:
        for pl in playlists:
            pl['username'] = self.userdb.getNameById(pl['userid'])
            pl['type'] = 'playlist'
            pl['age'] = curr_time - pl['created']
        if sortby[0] == '-':
            is_reverse = True
            sortby = sortby[1:]
        if not sortby in ('username', 'age', 'title', 'default'):
            sortby = 'created'
        if sortby == 'default':
            sortby = 'age'
            is_reverse = False
        playlists = sorted(playlists, key=lambda x: x[sortby], reverse = is_reverse)
        return playlists

    def api_logout(self):
        cherrypy.lib.sessions.expire()
    api_logout.no_auth = True

    def api_downloadpls(self, plid, hostaddr):
        userid = self.getUserId()
        pls = self.playlistdb.createPLS(plid=plid, userid=userid, addrstr=hostaddr)
        name = self.playlistdb.getName(plid, userid)
        if pls and name:
            return self.serve_string_as_file(pls, name+'.pls')
    api_downloadpls.binary = True

    def api_downloadm3u(self, plid, hostaddr):
        userid = self.getUserId()
        pls = self.playlistdb.createM3U(plid=plid, userid=userid, addrstr=hostaddr)
        name = self.playlistdb.getName(plid, userid)
        if pls and name:
            return self.serve_string_as_file(pls, name+'.m3u')
    api_downloadm3u.binary = True

    def export_playlists(self, format, all=False, hostaddr=''):
        userid = self.getUserId()
        if not userid:
            raise cherrypy.HTTPError(401, _("Please log in"))
        hostaddr = (hostaddr.strip().rstrip('/') + cherry.config['server.rootpath']).rstrip('/')

        format = format.lower()
        if format == 'm3u':
            filemaker = self.playlistdb.createM3U
        elif format == 'pls':
            filemaker = self.playlistdb.createPLS
        else:
            raise cherrypy.HTTPError(400,
                _('Unknown playlist format: {format!r}').format(format=format))

        playlists = self.playlistdb.showPlaylists(userid, include_public=all)
        if not playlists:
            raise cherrypy.HTTPError(404, _('No playlists found'))

        with MemoryZipFile() as zip:
            for pl in playlists:
                plid = pl['plid']
                plstr = filemaker(plid=plid, userid=userid, addrstr=hostaddr)
                name = self.playlistdb.getName(plid, userid) + '.' + format
                if not pl['owner']:
                    username = self.userdb.getNameById(pl['userid'])
                    name =  username + '/' + name
                zip.writestr(name, plstr)

        zipmime = 'application/x-zip-compressed'
        zipname = 'attachment; filename="playlists.zip"'
        cherrypy.response.headers["Content-Type"] = zipmime
        cherrypy.response.headers['Content-Disposition'] = zipname
        return zip.getbytes()
    export_playlists.exposed = True

    def api_getsonginfo(self, path):
        basedir = cherry.config['media.basedir']
        abspath = os.path.join(basedir, path)
        return json.dumps(metainfo.getSongInfo(abspath).dict())

    def api_getencoders(self):
        return json.dumps(audiotranscode.getEncoders())

    def api_getdecoders(self):
        return json.dumps(audiotranscode.getDecoders())

    def api_transcodingenabled(self):
        return json.dumps(cherry.config['media.transcode'])

    def api_updatedb(self):
        self.model.updateLibrary()
        return 'success'

    def api_getconfiguration(self):
        clientconfigkeys = {
            'transcodingenabled': cherry.config['media.transcode'],
            'fetchalbumart': cherry.config['media.fetch_album_art'],
            'isadmin': cherrypy.session['admin'],
            'username': cherrypy.session['username'],
            'servepath': 'serve/',
            'transcodepath': 'trans/',
            'auto_login': self.autoLoginActive(),
            'version': cherry.REPO_VERSION or cherry.VERSION,
        }
        if cherry.config['media.transcode']:
            decoders = list(self.model.transcoder.available_decoder_formats())
            clientconfigkeys['getdecoders'] = decoders
            encoders = list(self.model.transcoder.available_encoder_formats())
            clientconfigkeys['getencoders'] = encoders
        else:
            clientconfigkeys['getdecoders'] = []
            clientconfigkeys['getencoders'] = []
        return clientconfigkeys

    def serve_string_as_file(self, string, filename):
        content_disposition = 'attachment; filename="'+filename+'"'
        cherrypy.response.headers["Content-Type"] = "application/x-download"
        cherrypy.response.headers["Content-Disposition"] = content_disposition
        return codecs.encode(string, "UTF-8")


def _save_and_release_session():
    """ workaround to cleanly release FileSessions in Cherrypy >= 3.3

        From https://github.com/devsnd/cherrymusic/issues/483:

        > CherryPy >=3.3.0 (up to current version, 3.6) makes it impossible to
        > explicitly release FileSession locks, because:

        > 1. FileSession.save() asserts that the session is locked; and

        > 2. _cptools.SessionTool always adds a hook to call sessions.save
        > before the response is finalized.

        > If we still want to release the session in a controller, I guess the
        > best way to work around this is to remove the hook before the
        > controller returns:
    """
    cherrypy.session.save()
    hooks = cherrypy.serving.request.hooks['before_finalize']
    forbidden = cherrypy.lib.sessions.save
    hooks[:] = [h for h in hooks if h.callback is not forbidden]
    # there's likely only one hook, since a 2nd call to save would always fail;
    # but let's be safe, and block all calls to save :)
