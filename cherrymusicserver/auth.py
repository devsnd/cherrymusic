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
import cherrypy

from cherrymusicserver import service


users = service.get('users')

#TODO : local auto login
#TODO : deny remote admin
#TODO : python2->3 session bug


#
# http://tools.cherrypy.org/wiki/AuthenticationAndAccessRestrictions
#

_SESSION_KEY = '_auth_uid'


def login(username, password):
    user = users.auth(username, password)
    cherrypy.session.regenerate()
    cherrypy.session[_SESSION_KEY] = user.uid
    cherrypy.request.user = user
    return user


def logout():
    cherrypy.lib.sessions.expire()
    cherrypy.session[_SESSION_KEY] = None
    cherrypy.request.user = None


def is_admin():
    return cherrypy.request.user.isadmin


def is_user(required_user):
    def condition():
        return required_user == cherrypy.request.user
    return condition


def check(*conditions):
    user = getattr(cherrypy.request, 'user', None)
    if not (user and user.is_valid is True):
        raise cherrypy.HTTPError(401)
    for condition in conditions:
        if not condition():
            raise cherrypy.HTTPError(403)
    return True


def check_tool(*args, **kwargs):
    """A tool that looks in config for 'auth.require'. If found and it
    is not None, a login is required and the entry is evaluated as a list of
    conditions that the user must fulfill"""
    conditions = cherrypy.request.config.get('auth.require', None)
    if conditions is not None:
        check(conditions)
cherrypy.tools.auth = cherrypy.Tool('before_handler', check_tool)


def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate
