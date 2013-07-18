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
from mock import *
from nose.tools import *

from cherrymusicserver import service
service.provide('users', 'i am the userservice stand-in')

from cherrymusicserver import auth


def no_login():
    auth.users = Mock()
    auth.cherrypy = Mock()
    auth.cherrypy.session = MagicMock()
    auth.cherrypy.request = Mock()

@with_setup(no_login)
def test_login_should_authenticate_credentials():
    auth.login('some_name', 'some_password')
    auth.users.auth.assert_called_with('some_name', 'some_password')


@with_setup(no_login)
def test_login_success_should_return_user():
    user = auth.users.auth.return_value = Mock()
    assert user is auth.login('some_name', 'some_password')


@with_setup(no_login)
def test_login_success_should_reset_session():
    auth.login('some_name', 'some_password')
    auth.cherrypy.session.regenerate.assert_called()


@with_setup(no_login)
def test_login_success_should_set_request_user():
    user = auth.users.auth.return_value = Mock()

    auth.login('some_name', 'some_password')

    auth.cherrypy.session.user.assert_equals(user)
