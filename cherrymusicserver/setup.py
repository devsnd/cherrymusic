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
import json
import subprocess

from cherrymusicserver import pathprovider
from cherrymusicserver import configuration as cfg

class SetupHandler:
    def index(self):
        return pathprovider.readRes('res/setup.html')
    index.exposed = True

    def saveconfig(self, values):
        config = cfg.from_defaults()
        try:
            if not os.path.exists(config.media.basedir.str):
                raise Exception('media.basedir')
            customcfg = cfg.from_dict(json.loads(values))
            config += customcfg
        except Exception as e:
            print(repr(e))      # whole exception
            print(e.args)       # error message (args[0]), etc.
            validAndConfigFileWritten = False
            raise cherrypy.HTTPError(400) #bad request
        else:
            cfg.write_to_file(config, pathprovider.configurationFile())
            validAndConfigFileWritten = True
        if validAndConfigFileWritten:
            cherrypy.engine.exit() #server shuts down slowly
            return '' #so request should still reach client...

    saveconfig.exposed = True
    
    def mockFeatureCheck(self):
        import random
        return bool(random.random()-0.5>0)
        
    def checkFeature(self, featurelist, feature):
        checkers = {
            'ImageMagick': (Feature('convert'), 'has-imagemagick', 'resizing of album covers'),
            'Vorbis Tools' : (Feature('oggenc'), 'has-has-vorbis-tools', 'encoding and decoding of OGGs'),
            'Lame': (Feature('lame'), 'has-lame', 'encoding and decoding of MP3s'),
            'FLAC': (Feature('flac'), 'has-flac', 'encoding and decoding of FLACs'),
            'mplayer':(Feature('mplayer'), 'has-mplayer', 'decoding OGG, MP3, FLAC, WMA and AAC'),
        }
        
        if feature in checkers:
            installed = checkers[feature][0]()
            idx = checkers[feature][1]
            msg = checkers[feature][2]
            if installed:
                text = 'enables '+msg
            else:
                text = 'leads to missing feature: '+msg
            featurelist.append([feature, installed, idx, text])
        
    def getfeatures(self):
        featurelist = []
        self.checkFeature(featurelist, 'ImageMagick')
        self.checkFeature(featurelist, 'Vorbis Tools')
        self.checkFeature(featurelist, 'Lame')
        self.checkFeature(featurelist, 'FLAC')
        #self.checkFeature(featurelist, 'mplayer')
        return json.dumps(featurelist)
    getfeatures.exposed = True
    
class Feature:
    def __init__(self, command):
        self.command = command
    def __call__(self):
        try:
            with open(os.devnull,'w') as devnull:
                subprocess.Popen([self.command],stdout=devnull, stderr=devnull)
            return True
        except OSError:
            return False

def configureAndStartCherryPy(port=8080):
        socket_host = "0.0.0.0"

        resourcedir = os.path.abspath(pathprovider.getResourcePath('res'))
    
        cherrypy.config.update({
            'server.socket_port': port,
            'log.error_file': os.path.join(pathprovider.getUserDataPath(), 'server.log'),
            'environment': 'production',
            'server.socket_host': socket_host,
            'server.thread_pool' : 30,
            'tools.sessions.on' : True,
            'tools.sessions.timeout' : 60 * 24,
            })

        cherrypy.tree.mount(SetupHandler(), '/',
            config={
                '/res': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': resourcedir,
                    'tools.staticdir.index': 'index.html',
                    'tools.caching.on' : False,
                },
                '/favicon.ico':{
                    'tools.staticfile.on' : True,
                    'tools.staticfile.filename' : resourcedir+'/favicon.ico',
                }
            }
        )
        print('Starting setup server on port %d ...' % port)
        print('Open your browser and put the server IP:%d in the address bar.'%port)
        print('If you run the server locally, use: localhost:%d'%port)

        cherrypy.lib.caching.expires(0) #disable expiry caching
        cherrypy.engine.timeout_monitor.frequency = 1
        cherrypy.engine.start()
        cherrypy.engine.block()
