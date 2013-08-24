#!/usr/bin/python3
# -*- coding: utf-8 -*- #
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2013 Tom Wallroth & Tilman Boerner
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

import cherrypy

from cherrymusicserver import log

class _guarded_session(object):
    ''' workaround for python2/python3 jump, filed bug in cherrypy
        https://bitbucket.org/cherrypy/cherrypy/issue/1216/sessions-python2-3-compability-unsupported
    '''

    def __enter__(self):
        return cherrypy.session

    def __exit__(self, exctype, exception, traceback):
        if exctype in (ValueError,):    # UnicodeDecodeError is also ValueError
            self.__drop_sessions()
            return True
        return False

    @staticmethod
    def __drop_sessions():
        log.w(
            'Dropping all sessions! Try not to change between python 2 and 3,\n'
            'everybody has to relogin now.')
        cherrypy.session.delete()


class current(_guarded_session):
    """Context Manager to access the current session with."""
    pass
