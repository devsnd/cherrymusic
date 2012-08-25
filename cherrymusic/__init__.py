
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

    def start(self):
        socket_host = "127.0.0.1" if config.server.localhost_only.bool else "0.0.0.0"
        error_file_path = os.path.join(os.path.dirname(__file__), config.server.logfile.str)
        currentserverpath = os.path.abspath(os.path.dirname(__file__))
        #check if theme is available in module
        themename = config.look.theme.str
        defaulttheme = 'zeropointtwo'
        themedir = os.path.join(currentserverpath, '..','themes',themename)
        #if not, use the theme in the homedir
        if not os.path.isdir(themedir):
            themedir = os.path.join(os.path.expanduser('~'),'.cherrymusic','themes',themename)
        #if not available use default theme
        if not os.path.isdir(themedir):
            themedir = os.path.join(currentserverpath, '..','themes',defaulttheme)

        if config.server.use_ssl.bool:
            cherrypy.config.update({
                'server.ssl_certificate': config.server.ssl_certificate.str,
                'server.ssl_private_key': config.server.ssl_private_key.str,
                'server.socket_port': config.server.ssl_port.int,
            })
            # Create second server for http redirect:
            redirecter = cherrypy._cpserver.Server()
            redirecter.socket_port=config.server.port.int
            redirecter._socket_host=socket_host
            redirecter.thread_pool=30
            redirecter.subscribe()
        else:
            cherrypy.config.update({
                'server.socket_port': config.server.port.int,
            })
            
        cherrypy.config.update({
            'log.error_file': error_file_path,
            'environment': 'production',
            "server.socket_host": socket_host,
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
                    'tools.staticdir.dir': themedir,
                    'tools.staticdir.index': 'index.html',
                },
                '/serve' :{
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': config.media.basedir.str,
                    'tools.staticdir.index': 'index.html',
                    'tools.encode.on' : True,
                    'tools.encode.encoding' : 'utf-8',
                },
        })
        print('Starting server on port %s ...' % config.server.port)
        cherrypy.engine.start()

    def pyopensslExists(self):
        try:
            import OpenSSL
            return True
        except ImportError:
            return False

    def serverless(self):
        cherrypy.server.unsubscribe()
        self.start()

    def server(self):
        cherrypy.config.update({'log.screen': True})
        self.start()

