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

import os
import cherrypy
import json
import subprocess
import threading

from cherrymusicserver import pathprovider
from cherrymusicserver import configuration as cfg


class SetupHandler:
    def index(self):
        return pathprovider.readRes('res/setup.html')
    index.exposed = True

    def saveconfig(self, values):
        collect_errors = cfg.error_collector()
        baseconfig = cfg.from_defaults()
        newconfig = json.loads(values, encoding='str')
        customcfg = baseconfig.replace(newconfig, collect_errors)
        if collect_errors:
            badkeys = (e.key for e in collect_errors)
            return json.dumps({"status": "error", 'fields': list(badkeys)})
        cfg.write_to_file(customcfg, pathprovider.configurationFile())
        # kill server in a second
        threading.Timer(1, lambda: cherrypy.engine.exit()).start()
        # so request should still reach client...
        return json.dumps({"status": "success"})

    saveconfig.exposed = True

    def mockFeatureCheck(self):
        import random
        return bool(random.random()-0.5 > 0)

    def checkFeature(self, featurelist, feature):
        checkers = {
            'ImageMagick':  (Feature('convert'),
                             'has-imagemagick',
                             _('resizing of album covers'),
                             _('The executable "convert" was not found in you PATH')),
            'Vorbis Tools': (Feature('oggenc'),
                             'has-has-vorbis-tools',
                             _('encoding and decoding of OGGs'),
                             _('The executables "oggenc" and "oggdec" were not found in you PATH')),
            'Lame':         (Feature('lame'),
                             'has-lame',
                             _('encoding and decoding of MP3s'),
                             _('The executable "lame" was not found in you PATH')),
            'FLAC':         (Feature('flac'),
                             'has-flac',
                             _('encoding and decoding of FLACs'),
                             _('The executable "flac" was not found in you PATH')),
            'mplayer':      (Feature('mplayer'),
                             'has-mplayer',
                             _('decoding OGG, MP3, FLAC, WMA and AAC'),
                             _('The executable "mplayer" was not found in you PATH')),
        }
        if feature in checkers:
            installed = checkers[feature][0]()
            idx = checkers[feature][1]
            msg = checkers[feature][2]
            explaination = checkers[feature][3]
            if installed:
                text = 'enables '+msg
            else:
                text = 'leads to missing feature: '+msg
            featurelist.append([feature, installed, idx, text, explaination])

    def getfeatures(self):
        featurelist = []
        self.checkFeature(featurelist, 'ImageMagick')
        self.checkFeature(featurelist, 'Vorbis Tools')
        self.checkFeature(featurelist, 'Lame')
        self.checkFeature(featurelist, 'FLAC')
        #self.checkFeature(featurelist, 'mplayer')
        return json.dumps(featurelist)
    getfeatures.exposed = True

    def ping(self):
        return "pong"
    ping.exposed = True


class Feature:
    def __init__(self, command):
        self.command = command

    def __call__(self):
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen([self.command],
                                 stdout=devnull,
                                 stderr=devnull)
            return True
        except OSError:
            return False


def configureAndStartCherryPy(port):
        if not port:
            port = 8080
        socket_host = "0.0.0.0"
        resourcedir = os.path.abspath(pathprovider.getResourcePath('res'))
        userdatapath = pathprovider.getUserDataPath()
        cherrypy.config.update({
            'server.socket_port': port,
            'log.error_file': os.path.join(userdatapath, 'server.log'),
            'environment': 'production',
            'server.socket_host': socket_host,
            'server.thread_pool': 30,
            'tools.sessions.on': True,
            'tools.sessions.timeout': 60 * 24,
        })
        resource_config = {
            '/res': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': resourcedir,
                'tools.staticdir.index': 'index.html',
                'tools.caching.on': False,
            },
            '/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': resourcedir+'/favicon.ico',
            }
        }
        cherrypy.tree.mount(SetupHandler(), '/', config=resource_config)
        print(_('''
Starting setup server on port {port} ...
Open your browser and put the server IP:{port} in the address bar.
If you run the server locally, use: localhost:{port}.
'''.format(port=port)))

        cherrypy.lib.caching.expires(0)
        cherrypy.engine.timeout_monitor.frequency = 1
        cherrypy.engine.start()
        cherrypy.engine.block()
