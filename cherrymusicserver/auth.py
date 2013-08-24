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

import cherrymusicserver as cherry
from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver import sessions


#
# see:
#   http://tools.cherrypy.org/wiki/AuthenticationAndAccessRestrictions
#

_SESSION_KEY = '_auth_uid'


class _ServiceProxy(object):

    def __init__(self, handle):
        self.__handle = handle

    def __getattr__(self, name):
        s = service.get(self.__handle)
        return getattr(s, name)


users = _ServiceProxy('users')


def login(username, password):
    user = users.auth(username, password)
    log.d('authenticated user %r', user.name)
    reject_remote_admin = not cherry.config['server.permit_remote_admin_login']
    if not _is_loopback_connection() and user.isadmin and reject_remote_admin:
        log.i('rejected remote login of admin user %r', user.name)
        user = _nobody()
    return _login(user)


def logout():
    with sessions.current() as session:
        cherrypy.lib.sessions.expire()
        try:
            del session[_SESSION_KEY]
        except KeyError:
            pass
        finally:
            try:
                del cherrypy.request.user
            except AttributeError:
                pass


def is_admin():
    user = current_user()
    return user and user.isadmin


def is_user(required_user):
    def condition():
        return required_user == current_user()
    return condition

_any = any
def any(*conditions):
    return lambda: _any(c() for c in conditions)


def check(*conditions):
    user = current_user()
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
        check(*conditions)
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


def current_user():
    user = _nobody()
    try:
        user = cherrypy.request.user
    except AttributeError:
        with sessions.current() as session:
            try:
                uid = session[_SESSION_KEY]
                user = users.getById(uid)
            except KeyError:
                user = _try_autologin()
            else:
                cherrypy.request.user = user
    return user


def _is_loopback_connection():
    log.i('remote ip: %r', cherrypy.request.remote.ip)
    return cherrypy.request.remote.ip in ('127.0.0.1', '::1')


def _try_autologin():
    if _is_loopback_connection() and cherry.config['server.localhost_auto_login']:
        return _login(users.getById(1))
    return _nobody()


def _login(user):
    bad_user = not user or not user.is_valid
    with sessions.current() as session:
        conflict = _SESSION_KEY in session and session[_SESSION_KEY] != user.uid
        if bad_user or conflict:
            logout()
            return _nobody()
        session.regenerate()
        session[_SESSION_KEY] = user.uid
    cherrypy.request.user = user
    log.i('logged in: %r', user.name)
    return user


def _nobody():
    return users.User.nobody()
