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

#python 2.6+ backward compability
from __future__ import unicode_literals

import cherrypy

from cherrymusicserver.api.v1.models import Model
from cherrymusicserver.api.v1.resources import Resource

def get_resource():
    return users()

class User(Model):

    name = Model.Field(None)
    roles = Model.Field([])


_userdb = {
    'adm': User(id=1, name='adm', roles=('admin' 'user')),
    'puh': User(id=22, name='puh', roles=('user' 'bear')),
}

class users(Resource):

    def GET(self, name=None):
        if name:
            if not name in _userdb:
                raise cherrypy.NotFound(name)
            return _userdb[name]
        return sorted(_userdb)
