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

import cherrypy

from cherrymusicserver import service
service.provide('users', 'userservice (replace by mock)')

from cherrymusicserver import auth


def no_login():
    auth.users = Mock()
    auth.cherrypy.session = MagicMock()
    if hasattr(auth.cherrypy.request, 'user'):
        del auth.cherrypy.request.user


def logged_in():
    no_login()
    user = Mock()
    user.is_valid = True
    auth.cherrypy.request.user = user


@with_setup(no_login)
@patch('cherrymusicserver.auth.cherrypy')
def test_login_should_authenticate_credentials(cherrypy):
    auth.login('some_name', 'some_password')
    auth.users.auth.assert_called_with('some_name', 'some_password')


@with_setup(no_login)
@patch('cherrymusicserver.auth.cherrypy')
def test_login_should_return_user(cherrypy):
    user = auth.users.auth.return_value = Mock()
    assert user is auth.login('some_name', 'some_password')


@with_setup(no_login)
@patch('cherrymusicserver.auth.cherrypy')
def test_login_should_reset_session(cherrypy):
    auth.login('some_name', 'some_password')
    cherrypy.session.regenerate.assert_called()


@with_setup(no_login)
@patch('cherrymusicserver.auth.cherrypy')
def test_login_should_set_request_user(cherrypy):
    user = auth.users.auth.return_value = Mock()

    auth.login('some_name', 'some_password')

    assert cherrypy.request.user is user


@with_setup(logged_in)
@patch('cherrymusicserver.auth.cherrypy')
def test_logout_should_unset_request_user_and_session(cherrypy):
    auth.logout()

    assert cherrypy.request.user is None, cherrypy.request.user
    cherrypy.session.__setitem__.assert_called


@with_setup(no_login)
@raises(cherrypy.HTTPError)
def test_check_should_fail_without_login():
    auth.check()


@with_setup(logged_in)
def test_check_should_return_true_with_login():
    assert auth.check() is True


@with_setup(logged_in)
def test_check_must_call_conditions():
    condition_one, condition_two = Mock(), Mock()

    auth.check(condition_one, condition_two)

    condition_one.assert_called
    condition_two.assert_called


@with_setup(logged_in)
@raises(cherrypy.HTTPError)
def test_check_must_fail_on_false_condition():
    auth.check(Mock(return_value=False))


@with_setup(logged_in)
@raises(cherrypy.HTTPError)
def test_check_must_fail_on_untrue_condition():
    auth.check(Mock(return_value=None))
