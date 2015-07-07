# -*- coding: utf-8 -*- #
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
Moves cherrymusic.conf to correct location in OS X

~/Application Support/cherrymusic => ~/Library/Application Support/cherrymusic

See https://github.com/devsnd/cherrymusic/issues/459
"""
#python 2.6+ backward compability
from __future__ import unicode_literals

import os
import shutil

def migrate():
    oldpath = os.path.join(os.path.expanduser('~'), 'Application Support', 'cherrymusic')
    newpath = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'cherrymusic')
    oldpath_exists = os.path.exists(oldpath)
    newpath_exists = os.path.exists(newpath)
    if oldpath_exists:
        if newpath_exists:
            # two data/conf directories, just warn and skip.
            print("""There are two different data/config directories,
but normally that shouldn't happen. The old and unused one is here:
%s
The currently used one is here:
%s
You can keep either one, and cherrymusic will figure it out on the next
start.""" % (oldpath, newpath))
        else:
            # standard migration case. old one exists, but new one
            # does not
            print('UPDATE: Moving config/data directory to new location...')
            shutil.move(oldpath, newpath)
            print('UPDATE: done.')
