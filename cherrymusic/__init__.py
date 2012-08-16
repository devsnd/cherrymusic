
#import pickle
#from time import time
#import hashlib

import os
import cherrypy

from cherrymusic import config
from cherrymusic import sqlitecache
from cherrymusic import cherrymodel
from cherrymusic import httphandler

class CherryMusic:
    def __init__(self):
        self.config = config.Config()
        self.db = sqlitecache.SQLiteCache(self.config)
        self.cherrymodel = cherrymodel.CherryModel(self.config,self.db)
        self.httphandler = httphandler.HTTPHandler(self.config,self.cherrymodel)
        self.server()

    def encrypt_pw(self,pw):
        #return hashlib.sha1(pw).hexdigest()
        return pw

    def start(self):
        currentserverpath = os.path.abspath(os.path.dirname(__file__))

        cherrypy.config.update({
            'log.error_file': os.path.join(os.path.dirname(__file__), 'site.log'),
            'environment': 'production',
            "server.socket_host": "0.0.0.0",
            'server.socket_port': 8080, #TODO make port avaiable in config
            })
        cherrypy.tree.mount(self.httphandler,'/',
            config={
                '/res': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': os.path.join(currentserverpath,'../res'),
                    'tools.staticdir.index': 'index.html',
                },
                '/'+self.config.config[self.config.HOSTALIAS]:{
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': self.config.config[self.config.BASEDIR],
                    'tools.staticdir.index': 'index.html',
                    'tools.encode.on' : True,
                    'tools.encode.encoding' : 'utf-8',
                },
                '/': {
                    'tools.basic_auth.on': True,
                    'tools.basic_auth.realm': 'Cherry Music',
                    'tools.basic_auth.users': self.config.config[self.config.USER],
                    'tools.basic_auth.encrypt': self.encrypt_pw
                }

        })
        print('Starting server on port 8080 ...') #TODO display actually used port
        cherrypy.engine.start()


    def serverless():
        cherrypy.server.unsubscribe()
        start(config)

    def server(self):
        cherrypy.config.update({'log.screen': True})
        self.start()

