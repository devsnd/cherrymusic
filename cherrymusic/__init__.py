
#import pickle
#from time import time
#import hashlib

import os
import cherrypy

from cherrymusic import configuration
from cherrymusic import configdb
from cherrymusic import sqlitecache
from cherrymusic import cherrymodel
from cherrymusic import httphandler

config = None

class CherryMusic:

    def __init__(self):
        self._init_config()
        self.db = sqlitecache.SQLiteCache()
        self.cherrymodel = cherrymodel.CherryModel(self.db)
        self.httphandler = httphandler.HTTPHandler(config,self.cherrymodel)
        self.server()


    def _init_config(self):
        global config
        cdb = configdb.ConfigDB()
        filecfg = configuration.from_configparser('./config')
        cdb.update(filecfg)
        config = cdb.load()


    def encrypt_pw(self, pw):
        #return hashlib.sha1(pw).hexdigest()
        return pw

    def start(self):
        currentserverpath = os.path.abspath(os.path.dirname(__file__))

        cherrypy.config.update({
            'log.error_file': os.path.join(os.path.dirname(__file__), config.server.logfile.str),
            'environment': 'production',
            "server.socket_host": "0.0.0.0",
            'server.socket_port': config.server.port.int,
            'tools.sessions.on' : True,
            })
        cherrypy.tree.mount(self.httphandler, '/',
            config={
                '/res': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': os.path.join(currentserverpath, '../res'),
                    'tools.staticdir.index': 'index.html',
                },
                '/theme': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': os.path.join(currentserverpath, '..','themes',config.look.theme.str),
                    'tools.staticdir.index': 'index.html',
                },
                '/serve' :{
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': config.media.basedir.str,
                    'tools.staticdir.index': 'index.html',
                    'tools.encode.on' : True,
                    'tools.encode.encoding' : 'utf-8',
                },
                #'/': {
                #    'tools.basic_auth.on': True,
                #    'tools.basic_auth.realm': 'Cherry Music',
                #    'tools.basic_auth.users': self.config.config[self.config.USER],
                #    'tools.basic_auth.encrypt': self.encrypt_pw
                #}

        })
        print('Starting server on port %s ...' % config.server.port)
        cherrypy.engine.start()


    def serverless(self):
        cherrypy.server.unsubscribe()
        self.start()

    def server(self):
        cherrypy.config.update({'log.screen': True})
        self.start()

