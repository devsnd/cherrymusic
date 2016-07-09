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

#python 2.6+ backward compability
from __future__ import unicode_literals

VERSION = "0.37.0"
__version__ = VERSION
DESCRIPTION = "an mp3 server for your browser"
LONG_DESCRIPTION = """CherryMusic is a music streaming
    server written in python. It's based on cherrypy and jPlayer.
    You can search your collection, create and share playlists with
    other users. It's able to play music on almost all devices since
    it happens in your browser and uses HTML5 for audio playback.
    """

from backport import input

import re
import os
import codecs
import sys
import threading
import signal

import gettext
from cherrymusicserver import pathprovider


if sys.version_info < (3,):
    gettext.install('default', unicode=True, localedir=pathprovider.getResourcePath('res/i18n'))
else:
    gettext.install('default', localedir=pathprovider.getResourcePath('res/i18n'))


# woraround for cherrypy 3.2.2:
# https://bitbucket.org/cherrypy/cherrypy/issue/1163/attributeerror-in-cherrypyprocessplugins
if sys.version_info >= (3, 3):
    threading._Timer = threading.Timer

import cherrypy

def version():
    return """CherryMusic Server {cm_version}

a standalone music server
Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner""".format(cm_version=VERSION)

def info():
    import locale
    import platform
    from audiotranscode import AudioTranscode
    audiotranscode = AudioTranscode()

    encoders = ['%s (%s)' % (enc.filetype, enc.command[0])
                for enc in audiotranscode.available_encoders]
    decoders = ['%s (%s)' % (enc.filetype, enc.command[0])
                for enc in audiotranscode.available_decoders]

    return """CherryMusic Server {cm_version}

CherryPy: {cp_version}
Python: {py_version}
Platform: {platform}

configuration dir:
    {confdir}
server data dir:
    {datadir}
static resources dir:
    {resourcedir}
server package dir:
    {packdir}
process working dir:
    {workdir}

locale: {locale}, default: {deflocale}
filesystem encoding: {fs_encoding}

Available Decoders:
    {decoders}
Available Encoders:
    {encoders}

(Do not parse this output.)""".format(
    cm_version=REPO_VERSION or VERSION,
    cp_version=cherrypy.__version__,
    py_version=platform.python_implementation() + ' ' + platform.python_version(),
    platform=platform.platform(),
    workdir=os.path.abspath(os.curdir),
    packdir=os.path.abspath(__path__[0]),
    confdir=pathprovider.getConfigPath(),
    datadir=pathprovider.getUserDataPath(),
    resourcedir=pathprovider.getResourcePath(''),
    locale=str(locale.getlocale()),
    deflocale=str(locale.getdefaultlocale()),
    fs_encoding=sys.getfilesystemencoding(),
    encoders='\n    '.join(encoders),
    decoders='\n    '.join(decoders),
)


cherrypyReqVersion = '3'
cherrypyCurrVersion = str(cherrypy.__version__)
if cherrypyCurrVersion < cherrypyReqVersion:
    print(_("""
cherrypy version is too old!
Current version: %(current_version)s
Required version: %(required_version)s or higher
""") % {'current_version': cherrypyCurrVersion,
        'required_version': cherrypyReqVersion})
    sys.exit(1)


# patch cherrypy crashing on startup because of double checking
# for loopback interface, see:
# https://bitbucket.org/cherrypy/cherrypy/issue/1100/cherrypy-322-gives-engine-error-when
def fake_wait_for_occupied_port(host, port):
    return
cherrypy.process.servers.wait_for_occupied_port = fake_wait_for_occupied_port
# end of port patch

# trying to detect the version to determine if we need to monkeypatch cherrypy
if cherrypy.__version__ == 'unknown':
    print(_(
        'Could not determine cherrypy version. Please install cherrypy '
        'using pip or your OS\'s package manager. Trying to detect version '
        'automatically.'
    ))
    try:
        # this decorator was added between 5.4 and 5.5
        # https://github.com/cherrypy/cherrypy/pull/1428
        # commit: dff09e92fb2e83fb4248826c9bc14cd3b6281706
        import cherrypy._cptools.register
        needs_serve_file_utf8_fix = False
    except ImportError:
        needs_serve_file_utf8_fix = True
else:
    cherrypy_version = tuple(int(v) for v in cherrypy.__version__.split('.'))
    needs_serve_file_utf8_fix = cherrypy_version < (5, 5)

if needs_serve_file_utf8_fix:
    # workaround for cherrypy < 5.5.0 not using unicode strings for URI, see:
    # https://bitbucket.org/cherrypy/cherrypy/issue/1148/wrong-encoding-for-urls-containing-utf-8
    cherrypy.lib.static.__serve_file = cherrypy.lib.static.serve_file

    def serve_file_utf8_fix(path, content_type=None, disposition=None,
                            name=None, debug=False):
        if sys.version_info >= (3,):
            #python3+
            # see also below: mirrored mangling of basedir for '/serve' static dir
            path = codecs.decode(codecs.encode(path, 'latin-1'), 'utf-8')
        return cherrypy.lib.static.__serve_file(path, content_type,
                                                disposition, name, debug)
    cherrypy.lib.static.serve_file = serve_file_utf8_fix
    # end of unicode workaround

from cherrymusicserver import configuration as cfg
config = None


from cherrymusicserver import cherrymodel
from cherrymusicserver import database
from cherrymusicserver import httphandler
from cherrymusicserver import log
from cherrymusicserver import migrations
from cherrymusicserver import playlistdb
from cherrymusicserver import service
from cherrymusicserver import sqlitecache
from cherrymusicserver import userdb
from cherrymusicserver import useroptiondb
from cherrymusicserver import api

import audiotranscode
MEDIA_MIMETYPES = audiotranscode.MIMETYPES.copy()
del audiotranscode


def setup_services():
    """ services can be used by other parts of the program to easily access
        different functions of cherrymusic by registering themselves as
        service.user

        See :mod:`~cherrymusicserver.services`.
    """
    service.provide('filecache', sqlitecache.SQLiteCache)
    service.provide('cherrymodel', cherrymodel.CherryModel)
    service.provide('playlist', playlistdb.PlaylistDB)
    service.provide('users', userdb.UserDB)
    service.provide('useroptions', useroptiondb.UserOptionDB)
    service.provide('dbconnector', database.sql.SQLiteConnector, kwargs={
        'datadir': pathprovider.databaseFilePath(''),
        'extension': 'db',
        'connargs': {'check_same_thread': False},
    })


def setup_config(override_dict=None):
    """ Updates the internal configuration using the following hierarchy:
        override_dict > file_config > default_config

        Notifies the user if there are new or deprecated configuration keys.

        See :mod:`~cherrymusicserver.configuration`.
    """
    defaults = cfg.from_defaults()
    filecfg = cfg.from_configparser(pathprovider.configurationFile())
    custom = defaults.replace(filecfg, on_error=log.e)
    if override_dict:
        custom = custom.replace(override_dict, on_error=log.e)
    global config
    config = custom
    _notify_about_config_updates(defaults, filecfg)


def run_general_migrations():
    """ Runs necessary migrations for CherryMusic data that is NOT kept inside
        of databases.

        This might however include relocating the database files tmhemselves,
        so general migrations should run before migrating the database content.

        See :mod:`~cherrymusicserver.migrations`.
    """
    migrations.check_and_migrate_all()


def migrate_databases():
    """ Makes sure CherryMusic's databases are up to date, migrating them if
        necessary.

        This might prompt the user for consent if a migration requires it and
        terminate the program if no consent is obtained.

        See :mod:`~cherrymusicserver.databases`.
    """
    db_is_ready = database.ensure_current_version(
        consentcallback=_get_user_consent_for_db_schema_update)
    if not db_is_ready:
        log.i(_("database schema update aborted. quitting."))
        sys.exit(1)


def start_server(cfg_override=None):
    """ Initializes and starts the CherryMusic server

        Args:
            cfg_override: A mapping of config keys to values to override those
                in the config file.
    """
    CherryMusic(cfg_override)


def create_user(username, password):
    """ Creates a non-admin user with given username and password """
    non_alnum = re.compile('[^a-z0-9]', re.IGNORECASE)
    if non_alnum.findall(username):
        log.e(_('usernames may only contain letters and digits'))
        return False
    return service.get('users').addUser(username, password, admin=False)

def delete_user(username):
    userservice = service.get('users')
    userid = userservice.getIdByName(username)
    if userid is None:
        log.e(_('user with the name "%s" does not exist!'), username)
        return False
    return userservice.deleteUser(userid)

def change_password(username, password):
    userservice = service.get('users')
    result = userservice.changePassword(username, password)
    return result == 'success'

def update_filedb(paths):
    """ Updates the file database in a separate thread,
        possibly limited to a sequence of paths inside media.basedir

        See :cls:`~cherrymusicserver.sqlitecache.SQLiteCache` methods
        :meth:`~cherrymusicserver.sqlitecache.SQLiteCache.full_update` and
        :meth:`~cherrymusicserver.sqlitecache.SQLiteCache.parital_update`.
    """
    cache = sqlitecache.SQLiteCache()
    target = cache.partial_update if paths else cache.full_update
    updater = threading.Thread(name='Updater', target=target, args=paths)
    updater.start()


def create_default_config_file(path):
    """ Creates or overwrites a default configuration file at `path` """
    cfg.write_to_file(cfg.from_defaults(), path)
    log.i(_('Default configuration file written to %(path)r'), {'path': path})


class CherryMusic:
    """Sets up services (configuration, database, etc) and starts the server"""
    def __init__(self, cfg_override=None):
        self.setup_config(cfg_override)
        setup_services()

        if config['media.basedir'] is None:
            print(_("Invalid basedir. Please provide a valid basedir path."))
            sys.exit(1)
        else:
            log.debug("Basedir is %r", config['media.basedir'])

        signal.signal(signal.SIGTERM, CherryMusic.stopAndCleanUp)
        signal.signal(signal.SIGINT, CherryMusic.stopAndCleanUp)
        if os.name == 'posix':
            signal.signal(signal.SIGHUP, CherryMusic.stopAndCleanUp)

        CherryMusic.create_pid_file()
        self.start_server(httphandler.HTTPHandler(config))
        CherryMusic.delete_pid_file()

    @classmethod
    def createUser(cls, credentials):
        """ .. deprecated:: > 0.34.1
                Use :func:`~cherrymusicserver.create_user` instead.
        """
        username, password = credentials
        return create_user(username, password)

    @classmethod
    def stopAndCleanUp(cls, signal=None, stackframe=None):
        """Delete the process id file and exit"""
        CherryMusic.delete_pid_file()
        print('Exiting...')
        sys.exit(0)

    @classmethod
    def create_pid_file(cls):
        """create a process id file, exit if it already exists"""
        if pathprovider.pidFileExists():
            with open(pathprovider.pidFile(), 'r') as pidfile:
                try:
                    if not sys.platform.startswith('win'):
                        # this call is only available on unix systems and throws
                        # an OSError if the process does not exist.
                        os.getpgid(int(pidfile.read()))
                    sys.exit(_("""============================================
Process id file %s already exists.
If you are sure that cherrymusic is not running, you can delete this file and restart cherrymusic.
============================================""") % pathprovider.pidFile())
                except OSError:
                    print('Stale process id file, removing.')
                    cls.delete_pid_file()
        with open(pathprovider.pidFile(), 'w') as pidfile:
            pidfile.write(str(os.getpid()))

    @classmethod
    def delete_pid_file(cls):
        """Delete the process id file, if it exists"""
        if pathprovider.pidFileExists():
            os.remove(pathprovider.pidFile())
        else:
            print(_("Error removing pid file, doesn't exist!"))

    @classmethod
    def setup_services(cls):
        """setup services: they can be used by other parts of the program
        to easily access different functions of cherrymusic by registering
        themselves as service.user

        .. deprecated:: > 0.34.1
            Use :func:`~cherrymusicserver.setup_services` instead.
        """
        setup_services()

    def setup_config(self, cfg_override):
        """.. deprecated:: > 0.34.1
            Use :func:`~cherrymusicserver.setup_config` instead.
        """
        setup_config(cfg_override)

    def setup_databases(self):
        """ check if the db schema is up to date

        .. deprecated:: > 0.34.1
            Use :func:`~cherrymusicserver.migrate_databases` instead.
         """
        migrate_databases()

    def start_server(self, httphandler):
        """use the configuration to setup and start the cherrypy server
        """
        cherrypy.config.update({'log.screen': True})
        ipv6_enabled = config['server.ipv6_enabled']
        if config['server.localhost_only']:
            socket_host = "::1" if ipv6_enabled else "127.0.0.1"
        else:
            socket_host = "::" if ipv6_enabled else "0.0.0.0"

        resourcedir = os.path.abspath(pathprovider.getResourcePath('res'))

        if config['server.ssl_enabled']:
            cert = pathprovider.absOrConfigPath(config['server.ssl_certificate'])
            pkey = pathprovider.absOrConfigPath(config['server.ssl_private_key'])
            cherrypy.config.update({
                'server.ssl_certificate': cert,
                'server.ssl_private_key': pkey,
                'server.socket_port': config['server.ssl_port'],
            })
            # Create second server for redirecting http to https:
            redirecter = cherrypy._cpserver.Server()
            redirecter.socket_port = config['server.port']
            redirecter._socket_host = socket_host
            redirecter.thread_pool = 10
            redirecter.subscribe()
        else:
            cherrypy.config.update({
                'server.socket_port': config['server.port'],
            })

        cherrypy.config.update({
            'log.error_file': os.path.join(
                pathprovider.getUserDataPath(), 'server.log'),
            'environment': 'production',
            'server.socket_host': socket_host,
            'server.thread_pool': 30,
            'tools.sessions.on': True,
            'tools.sessions.timeout': 60 * 24,
        })

        if not config['server.keep_session_in_ram']:
            sessiondir = os.path.join(
                pathprovider.getUserDataPath(), 'sessions')
            if not os.path.exists(sessiondir):
                os.mkdir(sessiondir)
            cherrypy.config.update({
                'tools.sessions.storage_type': "file",
                'tools.sessions.storage_path': sessiondir,
            })
        basedirpath = config['media.basedir']
        if sys.version_info < (3,0):
            basedirpath = codecs.encode(basedirpath, 'utf-8')
            scriptname = codecs.encode(config['server.rootpath'], 'utf-8')
        else:
            # fix cherrypy unicode issue (only for Python3)
            # see patch to cherrypy.lib.static.serve_file way above and
            # https://bitbucket.org/cherrypy/cherrypy/issue/1148/wrong-encoding-for-urls-containing-utf-8
            basedirpath = codecs.decode(codecs.encode(basedirpath, 'utf-8'), 'latin-1')
            scriptname = config['server.rootpath']
        cherrypy.tree.mount(
            httphandler, scriptname,
            config={
                '/res': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': resourcedir,
                    'tools.staticdir.index': 'index.html',
                    'tools.caching.on': False,
                    'tools.gzip.mime_types': ['text/html', 'text/plain', 'text/javascript', 'text/css'],
                    'tools.gzip.on': True,
                },
                '/serve': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': basedirpath,
                    # 'tools.staticdir.index': 'index.html',    if ever needed: in py2 MUST utf-8 encode
                    'tools.staticdir.content_types': MEDIA_MIMETYPES,
                    'tools.encode.on': True,
                    'tools.encode.encoding': 'utf-8',
                    'tools.caching.on': False,
                    'tools.cm_auth.on': True,
                    'tools.cm_auth.httphandler': httphandler,
                },
                '/favicon.ico': {
                    'tools.staticfile.on': True,
                    'tools.staticfile.filename': resourcedir + '/img/favicon.ico',
                }})
        api.v1.mount('/api/v1')
        log.i(_('Starting server on port %s ...') % config['server.port'])

        cherrypy.lib.caching.expires(0)  # disable expiry caching
        cherrypy.engine.start()
        cherrypy.engine.block()


def _cm_auth_tool(httphandler):
    if not httphandler.isAuthorized():
        raise cherrypy.HTTPError(403)
cherrypy.tools.cm_auth = cherrypy.Tool(
    'before_handler', _cm_auth_tool, priority=70)
    # priority=70 -->> make tool run after session is locked (at 50)


def _get_user_consent_for_db_schema_update(reasons):
    """Ask the user if the database schema update should happen now
    """
    import textwrap
    wrap = lambda r: os.linesep.join(
        textwrap.wrap(r, initial_indent=' - ', subsequent_indent="   "))
    msg = _("""
==========================================================================
A database schema update is needed and requires your consent.

{reasons}

To continue without changes, you need to downgrade to an earlier
version of CherryMusic.

To backup your database files first, abort for now and find them here:

{dblocation}

==========================================================================
Run schema update? [y/N]: """).format(
        reasons=(2 * os.linesep).join(wrap(r) for r in reasons),
        dblocation='\t' + pathprovider.databaseFilePath(''))
    return input(msg).lower().strip() in ('y',)


def _notify_about_config_updates(default, known_config):
    """check if there are new or deprecated configuration keys in
    the config file
    """
    new = []
    deprecated = []
    transform = lambda s: '[{0}]: {2}'.format(*(s.partition('.')))

    for property in cfg.to_list(default):
        if property.key not in known_config and not property.hidden:
            new.append(transform(property.key))
    for property in cfg.to_list(known_config):
        if property.key not in default:
            deprecated.append(transform(property.key))

    if new:
        log.i(_('''New configuration options available:
                    %s
                Using default values for now.'''),
              '\n\t\t\t'.join(new))
    if deprecated:
        log.i(_('''The following configuration options are not used anymore:
                    %s'''),
              '\n\t\t\t'.join(deprecated))
    if new or deprecated:
        log.i(_('Start with --newconfig to generate a new default config'
                ' file next to your current one.'))


def _get_version_from_git():
    """ Returns more precise version string based on the current git HEAD,
        or None if not possible.
    """
    if not os.path.isdir('.git'):
        return None
    def fetch(cmdname):
        import re
        from subprocess import Popen, PIPE
        cmd = {
            'branch': ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            'version': ['git', 'describe', '--tags'],
            'date': ['git', 'log', '-1', '--format=%cd'],
        }
        unwanted_characters = re.compile('[^\w.-]+')
        try:
            with open(os.devnull, 'w') as devnull:
                p = Popen(cmd[cmdname], stdout=PIPE, stderr=devnull)
                out, err = p.communicate()  # blocks until process terminates
        except:
            return None
        if out:
            out = out.decode('ascii', 'ignore')
            out = unwanted_characters.sub('', out).strip()
        return out
    branch = fetch('branch')
    version = fetch('version')
    if branch and version and '-' in version:
        version, patchlevel = version.split('-', 1)
        if version == VERSION:  # sanity check: latest tag is for VERSION
            return '{0}+{1}-{2}'.format(version, branch, patchlevel)
    return None

REPO_VERSION = _get_version_from_git()
