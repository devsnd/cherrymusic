#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2015 Tom Wallroth & Tilman Boerner
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
"""
This script is used to download cherrymusic dependencies on first startup.
"""

try:
    import urllib.request
except ImportError:
    from backport import urllib
from backport import input
import tempfile
import tarfile
import shutil
import os

class DependencyInstaller:
    def __init__(self):
        self.cherrymusicfolder = os.path.dirname(os.path.dirname(__file__))

    def install_cherrypy(self):
        """
        cherrypy releases: https://bitbucket.org/cherrypy/cherrypy/downloads
        """
        cherrypygitcommit = "586bee7ac445"
        cherrypyurl = "https://bitbucket.org/cherrypy/cherrypy/get/%s.tar.gz" % cherrypygitcommit
        cherrypysubfolder = os.path.join('cherrypy-cherrypy-%s'%cherrypygitcommit,'cherrypy')
        cherrypytempfile = os.path.join(tempfile.gettempdir(),'cherrypy.tar.gz')
        cherrypytempdir =  self.tmpdir('cherrypy')
        print('Downloading cherrypy...')
        self.dl(cherrypyurl, cherrypytempfile)
        print('Extracting %s ' % cherrypytempfile)
        tarc = tarfile.open(cherrypytempfile,'r:gz')
        tarc.extractall(cherrypytempdir)
        tarc.close()
        print('Copying cherrypy module inside cherrymusic folder (%s)...' % self.cherrymusicfolder)
        moduledir = os.path.join(cherrypytempdir,cherrypysubfolder)
        shutil.copytree(moduledir,os.path.join(self.cherrymusicfolder,'cherrypy'))
        print('Cleaning up temporary files...')
        shutil.rmtree(cherrypytempdir)
        os.remove(cherrypytempfile)

    def tmpdir(self, name):
        tempdirpath = os.path.join(tempfile.gettempdir(),name)
        if os.path.exists(tempdirpath):
            print("Directory %s already exists." % tempdirpath)
            if 'y' == input('Do you want to delete its contents and proceed? [y/n]'):
                shutil.rmtree(tempdirpath)
            else:
                print("Cannot install dependency.")
                exit(1)
        os.mkdir(tempdirpath)
        return tempdirpath

    def dl(self,url,target):
         with open(target, 'wb') as f:
            urlhandler = urllib.request.urlopen(urllib.request.Request(url))
            f.write(urlhandler.read())


def bootstrap():
    import sys
    try:
        import cherrypy
    except ImportError:
        print('''
        CherryMusic needs the module "cherrypy" to run. You should install it
        using the package manager of your OS. Alternatively cherrymusic can
        download it for you and put it in the folder in which currently
        CherryMusic resides.
        ''')
        if input("Download cherrypy now? (y/n)") == 'y':
            inst = DependencyInstaller()
            inst.install_cherrypy()
            print('Successfully installed cherrymusic dependencies! You can now start cherrymusic.')
        else:
            sys.exit(1)
