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

#python 2.6+ backward compability
from __future__ import unicode_literals

import sys
import threading

# woraround for cherrypy 3.2.2:
# https://bitbucket.org/cherrypy/cherrypy/issue/1163/attributeerror-in-cherrypyprocessplugins
if sys.version_info >= (3, 3):
    threading._Timer = threading.Timer

import os
import codecs
import cherrypy

cherrypyReqVersion = '3'
cherrypyCurrVersion = str(cherrypy.__version__)
if cherrypyCurrVersion < cherrypyReqVersion:
    print("""
cherrypy version is too old!
Current version: %s
Required version: %s or higher
""" % (cherrypyCurrVersion, cherrypyReqVersion))
    sys.exit(1)


# patch cherrypy crashing on startup because of double checking
# for loopback interface, see:
# https://bitbucket.org/cherrypy/cherrypy/issue/1100/cherrypy-322-gives-engine-error-when
def fake_wait_for_occupied_port(host, port):
    return
cherrypy.process.servers.wait_for_occupied_port = fake_wait_for_occupied_port
# end of port patch

# workaround for cherrypy not using unicode strings for URI, see:
# https://bitbucket.org/cherrypy/cherrypy/issue/1148/wrong-encoding-for-urls-containing-utf-8
cherrypy.lib.static.__serve_file = cherrypy.lib.static.serve_file


def serve_file_utf8_fix(path, content_type=None, disposition=None,
                        name=None, debug=False):
    path = codecs.decode(codecs.encode(path, 'latin-1'), 'utf-8')
    return cherrypy.lib.static.__serve_file(path, content_type, disposition,
                                            name, debug)

cherrypy.lib.static.serve_file = serve_file_utf8_fix
# end of unicode workaround

from cherrymusicserver import configuration
config = None


from cherrymusicserver import cherrymodel
from cherrymusicserver import database
from cherrymusicserver import httphandler
from cherrymusicserver import log
from cherrymusicserver import pathprovider
from cherrymusicserver import playlistdb
from cherrymusicserver import service
from cherrymusicserver import sqlitecache
from cherrymusicserver import userdb
from cherrymusicserver import useroptiondb
import cherrymusicserver.browsersetup

VERSION = "0.24.1"
DESCRIPTION = "an mp3 server for your browser"
LONG_DESCRIPTION = """CherryMusic is a music streaming
    server written in python. It's based on cherrypy and jPlayer.
    You can search your collection, create and share playlists with
    other users. It's able to play music on almost all devices since
    it happens in your browser and uses HTML5 for audio playback.
    """


class CherryMusic:

    def __init__(self, update=None, createNewConfig=False, dropfiledb=False,
                 setup=False, cfg_override={}):
        self.setup_services()
        self.setup_config(createNewConfig, setup, cfg_override)
        self.setup_databases(update, dropfiledb, setup)
        self.server(httphandler.HTTPHandler(config))

    @classmethod
    def setup_services(cls):
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

    def setup_config(self, createNewConfig, browsersetup, cfg_override):
        if browsersetup:
            port = cfg_override.pop('server.port', False)
            cherrymusicserver.browsersetup.configureAndStartCherryPy(port)
        if createNewConfig:
            newconfigpath = pathprovider.configurationFile() + '.new'
            configuration.write_to_file(configuration.from_defaults(),
                                        newconfigpath)
            log.i('New configuration file was written to:{br}{path}'.format(
                path=newconfigpath,
                br=os.linesep
            ))
            sys.exit(0)
        if not pathprovider.configurationFileExists():
            if pathprovider.fallbackPathInUse():   # temp. remove @ v0.30 or so
                self.printMigrationNoticeAndExit()
            else:
                configuration.write_to_file(configuration.from_defaults(),
                                            pathprovider.configurationFile())
                self.printWelcomeAndExit()
        self._init_config(cfg_override)

    def setup_databases(self, update, dropfiledb, setup):
        if dropfiledb:
            update = ()
            database.resetdb(sqlitecache.DBNAME)
        if setup:
            update = update or ()
        db_is_ready = database.ensure_current_version(
            consentcallback=self._get_user_consent_for_db_schema_update)
        if not db_is_ready:
            log.i("database schema update aborted. quitting.")
            sys.exit(1)
        if update is not None:
            cacheupdate = threading.Thread(name="Updater",
                                           target=self._update_if_necessary,
                                           args=(update,))
            cacheupdate.start()
            # self._update_if_necessary(update)
            if not setup:
                sys.exit(0)

    @staticmethod
    def _get_user_consent_for_db_schema_update(reasons):
        import textwrap
        wrap = lambda r: os.linesep.join(
            textwrap.wrap(r, initial_indent=' - ', subsequent_indent="   "))
        msg = """
==========================================================================
A database schema update is needed and requires your consent.

{reasons}

To continue without changes, you need to downgrade to an earlier
version of CherryMusic.

To backup your database files first, abort for now and find them here:

{dblocation}

==========================================================================
Run schema update? [y/N]: """.format(
            reasons=(2 * os.linesep).join(wrap(r) for r in reasons),
            dblocation='\t' + pathprovider.databaseFilePath(''))
        return input(msg).lower().strip() in ('y',)

    def _update_if_necessary(self, update):
        cache = sqlitecache.SQLiteCache()
        if update:
            cache.partial_update(*update)
        elif update is not None:
            cache.full_update()

    def _init_config(self, override_dict):
        global config
        defaultcfg = configuration.from_defaults()
        override = configuration.from_dict(override_dict)
        configFilePath = pathprovider.configurationFile()
        log.d('loading configuration from %s', configFilePath)
        filecfg = configuration.from_configparser(configFilePath)
        config = defaultcfg.replace(filecfg).replace(override)
        self._check_for_config_updates(filecfg)

    def _check_for_config_updates(self, known_config):
        new = []
        deprecated = []
        default = configuration.from_defaults()
        transform = lambda s: '[{0}]: {2}'.format(*(s.partition('.')))

        for property in configuration.to_list(default):
            if property.key not in known_config and not property.hidden:
                new.append(transform(property.key))
        for property in configuration.to_list(known_config):
            if property.key not in default:
                deprecated.append(transform(property.key))

        if new:
            log.i('''New configuration options available:
                        %s
                    Using default values for now.''',
                  '\n\t\t\t'.join(new))
        if deprecated:
            log.i('''The following configuration options are not used anymore:
                        %s''',
                  '\n\t\t\t'.join(deprecated))
        if new or deprecated:
            log.i('Start with --newconfig to generate a new default config'
                  ' file next to your current one.')

    def printMigrationNoticeAndExit(self):  # temp. remove @ v0.30 or so
        print("""
==========================================================================
Oops!

CherryMusic changed some file locations while you weren't looking.
(To better comply with best practices, if you wanna know.)

To continue, please move the following:

    $ mv {src} {tgt}""".format(
            src=os.path.join(pathprovider.fallbackPath(), 'config'),
            tgt=pathprovider.configurationFile()) + """

    $ mv {src} {tgt}""".format(
            src=os.path.join(pathprovider.fallbackPath(), '*'),
            tgt=pathprovider.getUserDataPath()) + """

Thank you, and enjoy responsibly. :)
==========================================================================
""")
        exit(1)

    def printWelcomeAndExit(self):
        print("""
==========================================================================
Welcome to CherryMusic """ + VERSION + """!

To get this party started, you need to edit the configuration file, which
resides under the following path:

    """ + pathprovider.configurationFile() + """

Then you can start the server and listen to whatever you like.
Have fun!
==========================================================================
""")
        exit(0)

    def start(self, httphandler):
        socket_host = "127.0.0.1" if config['server.localhost_only'] else "0.0.0.0"

        resourcedir = os.path.abspath(pathprovider.getResourcePath('res'))

        if config['server.ssl_enabled']:
            cherrypy.config.update({
                'server.ssl_certificate': config['server.ssl_certificate'],
                'server.ssl_private_key': config['server.ssl_private_key'],
                'server.socket_port': config['server.ssl_port'],
            })
            # Create second server for http redirect:
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

        cherrypy.tree.mount(
            httphandler, '/',
            config={
                '/res': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': resourcedir,
                    'tools.staticdir.index': 'index.html',
                    'tools.caching.on': False,
                },
                '/serve': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': config['media.basedir'],
                    'tools.staticdir.index': 'index.html',
                    'tools.encode.on': True,
                    'tools.encode.encoding': 'utf-8',
                    'tools.caching.on': False,
                },
                '/favicon.ico': {
                    'tools.staticfile.on': True,
                    'tools.staticfile.filename': resourcedir + '/favicon.ico',
                }})
        log.i('Starting server on port %s ...' % config['server.port'])

        cherrypy.lib.caching.expires(0)  # disable expiry caching
        cherrypy.engine.start()
        cherrypy.engine.block()

    def server(self, httphandler):
        cherrypy.config.update({'log.screen': True})
        self.start(httphandler)
