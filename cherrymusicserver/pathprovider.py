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
import sys
import base64
import codecs

def getUserDataPath():
    if sys.platform.startswith('linux'): #linux
        userdata = os.path.join(os.environ['XDG_DATA_HOME'],'cherrymusic')
    elif sys.platform.startswith('win'): # windows
        userdata = os.path.join(os.environ['APPDATA'],'cherrymusic')
    elif sys.platform.startswith('darwin'): # osx
        userdata = os.path.join(os.path.expanduser('~'),'Application Support','cherrymusic')
    else:
        userdata = os.path.join(os.path.expanduser('~'), '.cherrymusic')
    assureFolderExists(userdata,['db','albumart','sessions'])
    return userdata

def getConfigPath():
    if len(sys.argv) > 2 and (sys.argv[1] == '-c' or sys.argv[1] == '--config-path') and os.path.exists(sys.argv[2]):
        return sys.argv[2]
    else:
        if sys.platform.startswith('linux'): #linux
            configpath = os.path.join(os.environ['XDG_CONFIG_HOME'], 'cherrymusic')
        elif sys.platform.startswith('win'): #windows
            configpath = os.path.join(os.environ['APPDATA'],'cherrymusic')
        elif sys.platform.startswith('darwin'): #osx
            configpath = os.path.join(os.path.expanduser('~'),'Application Support','cherrymusic')
        else:
            configpath = os.path.join(os.path.expanduser('~'), '.cherrymusic')
        assureFolderExists(configpath)
        return configpath

def configurationFile():
    return os.path.join(getConfigPath(), 'config')

def configurationFileExists():
    return os.path.exists(configurationFile())

def databaseFilePath(filename):
    configdir = os.path.join(getUserDataPath(), 'db')
    if not os.path.exists(configdir):
        os.makedirs(configdir)
    configpath = os.path.join(configdir, filename)
    return configpath
    
def albumArtFilePath(directorypath):
    albumartcachepath = os.path.join(getUserDataPath(), 'albumart')
    if not os.path.exists(albumartcachepath):
        os.makedirs(albumartcachepath)
    configpath = os.path.join(albumartcachepath, base64encode(directorypath))
    return configpath

def base64encode(s):
    return codecs.decode(base64.b64encode(codecs.encode(s,'UTF-8')),'UTF-8')
    
def base64decode(s):
    return codecs.decode(base64.b64decode(s),'UTF-8')

def assureFolderExists(folder,subfolders=['']):
    for subfolder in subfolders:
        dirpath = os.path.join(folder, subfolder)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

def readRes(path):
    with open(getResourcePath(path)) as f:
        return f.read()

def getResourcePath(path):
    #check share first
    resourceprefix = os.path.join(sys.prefix, 'share', 'cherrymusic')
    respath = os.path.join(resourceprefix, path)
    if not os.path.exists(respath):
        #log.w("Couldn't find " + respath + ". Trying local install path.")
        #otherwise check local install
        resourceprefix = os.path.dirname(os.path.dirname(__file__))
        respath = os.path.join(resourceprefix, path)
    if not os.path.exists(respath):
        #log.w("Couldn't find " + respath + ". Trying home dir.")
        #lastly check homedir
        resourceprefix = getUserDataPath()
        respath = os.path.join(resourceprefix, path)
    if not os.path.exists(respath):
        raise ResourceNotFound("Couldn't locate '" + path + "'!")
    return os.path.join(resourceprefix, path)

class ResourceNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

def filename(path, pathtofile=False):
    if pathtofile:
        return os.path.split(path)[0]
    else:
        return os.path.split(path)[1]

def stripext(filename):
    if '.' in filename:
        return filename[:filename.rindex('.')]
    return filename
