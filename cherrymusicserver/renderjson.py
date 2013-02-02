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

"""
This class encapsulates all values returned by the cherrymodel
to be served as json to the client.
"""

import json

import cherrymusicserver as cherry
from cherrymusicserver import util, pathprovider
from urllib.parse import quote

class JSON(object):

    def __init__(self):
        pass


    def render(self, musicentries):
        retlist = []
        for entry in musicentries:
            if entry.compact:
                #compact
                retlist.append({'type':'compact', 'urlpath':entry.path,'label':entry.repr})
            elif entry.dir:
                #dir
                simplename = pathprovider.filename(entry.path)
                retlist.append({'type':'dir', 'path':entry.path,'label':simplename})
            else:
                #file
                simplename = pathprovider.filename(entry.path)
                urlpath = quote('/serve/' + entry.path);
                retlist.append({'type':'file',
                                'urlpath':urlpath,
                                'path':entry.path,
                                'label':simplename})
        return json.dumps(retlist)
