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

import os
import cherrypy
import threading

"""patch cherrypy crashing on startup because of double checking
for loopback interface, see:
https://bitbucket.org/cherrypy/cherrypy/issue/1100/cherrypy-322-gives-engine-error-when
"""
def fake_wait_for_occupied_port(host, port):
    return
cherrypy.process.servers.wait_for_occupied_port = fake_wait_for_occupied_port

from cherrymusicserver import configuration
from cherrymusicserver import sqlitecache
from cherrymusicserver import cherrymodel
from cherrymusicserver import httphandler
from cherrymusicserver import util
from cherrymusicserver import pathprovider
from cherrymusicserver import log
import cherrymusicserver.setup

config = None
VERSION = "0.23.0"
DESCRIPTION = "an mp3 server for your browser"
LONG_DESCRIPTION = """CherryMusic is a music streaming
    server written in python. It's based on cherrypy and jPlayer.
    You can search your collection, create and share playlists with
    other users. It's able to play music on almost all devices since
    it happends in your browser and uses HTML5 for audio playback.
    """

class CherryMusic:

    def __init__(self, update=None, createNewConfig=False, dropfiledb=False, setup=False):
        if setup:
            cherrymusicserver.setup.configureAndStartCherryPy()
        if createNewConfig:
            newconfigpath = pathprovider.configurationFile() + '.new'
            configuration.write_to_file(configuration.from_defaults(), newconfigpath)
            log.i('''New configuration file was written to:
''' + newconfigpath)
            exit(0)
        if not pathprovider.configurationFileExists():
            if pathprovider.fallbackPathInUse():   # temp. remove @ v0.30 or so
                self.printMigrationNoticeAndExit()
            else:
                configuration.write_to_file(configuration.from_defaults(), pathprovider.configurationFile())
                self.printWelcomeAndExit()
        self._init_config()
        self.db = sqlitecache.SQLiteCache(pathprovider.databaseFilePath('cherry.cache.db'))

        if not update == None or dropfiledb:
            CherryMusic.UpdateThread(self.db,update,dropfiledb).start()
        else:
            self.cherrymodel = cherrymodel.CherryModel(self.db)
            self.httphandler = httphandler.HTTPHandler(config, self.cherrymodel)
            self.server()

    class UpdateThread(threading.Thread):
        def __init__(self, db, update,dropfiledb):
            threading.Thread.__init__(self)
            self.db = db
            self.dropfiledb = dropfiledb
            self.update = update #command line switch
        def run(self):
            if self.dropfiledb:
                self.db.drop_tables()
            dbLayoutChangesOrCreation = self.db.create_and_alter_tables()
            if dbLayoutChangesOrCreation:
                self.db.full_update()
            elif self.update:
                self.db.partial_update(*self.update)
            elif self.update is not None:
                self.db.full_update()

    def _init_config(self):
        global config
        defaultcfg = configuration.from_defaults()
        configFilePath = pathprovider.configurationFile()
        log.d('loading configuration from %s', configFilePath)
        filecfg = configuration.from_configparser(configFilePath)
        config = defaultcfg + filecfg
        self._check_for_config_updates(filecfg)

    def _check_for_config_updates(self, known_config):
        new = []
        deprecated = []
        default = configuration.from_defaults()
        transform = lambda s: '[{0}]: {2}'.format(*(s.partition('.')))

        for property in configuration.to_list(default):     #@ReservedAssignment
            if property.name not in known_config and not property.hidden:
                new.append(transform(property.name))
        for property in configuration.to_list(known_config): #@ReservedAssignment
            if property.name not in default:
                deprecated.append(transform(property.name))

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
            log.i('''Start with --newconfig to generate a new default config file next to your current one.
                  ''',
            )

    def printMigrationNoticeAndExit(self):  # temp. remove @ v0.30 or so
        print("""
==========================================================================
Oops!

CherryMusic changed some file locations while you weren't looking.
(To better comply with best practices, if you wanna know.)

To continue, please move the following:

    $ mv """ + os.path.join(pathprovider.fallbackPath(), 'config') + ' ' +
        pathprovider.configurationFile() + """

    $ mv """ + os.path.join(pathprovider.fallbackPath(), '*') + ' ' +
        pathprovider.getUserDataPath() + """

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

    def start(self):
        socket_host = "127.0.0.1" if config.server.localhost_only.bool else "0.0.0.0"

        resourcedir = os.path.abspath(pathprovider.getResourcePath('res'))

        if config.server.ssl_enabled.bool:
            cherrypy.config.update({
                'server.ssl_certificate': config.server.ssl_certificate.str,
                'server.ssl_private_key': config.server.ssl_private_key.str,
                'server.socket_port': config.server.ssl_port.int,
            })
            # Create second server for http redirect:
            redirecter = cherrypy._cpserver.Server()
            redirecter.socket_port = config.server.port.int
            redirecter._socket_host = socket_host
            redirecter.thread_pool = 10
            redirecter.subscribe()
        else:
            cherrypy.config.update({
                'server.socket_port': config.server.port.int,
            })

        cherrypy.config.update({
            'log.error_file': os.path.join(pathprovider.getUserDataPath(), 'server.log'),
            'environment': 'production',
            'server.socket_host': socket_host,
            'server.thread_pool' : 30,
            'tools.sessions.on' : True,
            'tools.sessions.timeout' : 60 * 24,
            })

        if not config.server.keep_session_in_ram.bool:
            sessiondir = os.path.join(pathprovider.getUserDataPath(), 'sessions')
            if not os.path.exists(sessiondir):
                os.mkdir(sessiondir)
            cherrypy.config.update({
                'tools.sessions.storage_type' : "file",
                'tools.sessions.storage_path' : sessiondir,
                })


        cherrypy.tree.mount(self.httphandler, '/',
            config={
                '/res': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': resourcedir,
                    'tools.staticdir.index': 'index.html',
                    'tools.caching.on' : False,
                },
                '/serve' :{
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': config.media.basedir.str,
                    'tools.staticdir.index': 'index.html',
                    'tools.encode.on' : True,
                    'tools.encode.encoding' : 'utf-8',
                    'tools.caching.on' : False,
                },
                '/favicon.ico':{
                    'tools.staticfile.on' : True,
                    'tools.staticfile.filename' : resourcedir+'/favicon.ico',
                }
        })
        log.i('Starting server on port %s ...' % config.server.port.str)

        cherrypy.lib.caching.expires(0) #disable expiry caching
        cherrypy.engine.start()
        cherrypy.engine.block()

    def serverless(self):
        cherrypy.server.unsubscribe()
        self.start()

    def server(self):
        cherrypy.config.update({'log.screen': True})
        self.start()
