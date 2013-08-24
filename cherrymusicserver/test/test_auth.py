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

from imp import reload
from collections import defaultdict

import cherrypy

from cherrymusicserver import auth
from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver import sessions
import cherrymusicserver as cherry

def init():
    cherry.config = defaultdict(lambda: None)

    userdb = Mock()
    userdb.getById.side_effect = mock_user_by_id
    userdb.auth.side_effect = mock_user_auth
    userdb.User.nobody = Mock(return_value=nobody)
    service.provide('users', userdb)

    auth.cherrypy = MagicMock()
    auth.cherrypy.HTTPError = cherrypy.HTTPError

    global sessiondir
    sessiondir = {}
    session = MagicMock()
    session.__setitem__.side_effect = session_set
    session.__getitem__.side_effect = session_get
    session.__delitem__.side_effect = session_del
    session.__enter__.return_value = session
    sessions.current = lambda: session

    init_request()


def init_request(ip='127.0.0.1'):
    auth.cherrypy.request = MagicMock()
    auth.cherrypy.request.remote = MagicMock()
    auth.cherrypy.request.remote.ip = ip
    del auth.cherrypy.request.user


def teardown_module():
    sessions.current = reload(sessions).current
    auth.cherrypy = reload(cherrypy)
    service.provide('users', None)
    cherry.config = None


def no_login():
    init()
    session_user(None)


def logged_in():
    init()
    session_user('some_user')


@with_setup(no_login)
def test_login_should_return_authentication_result():
    assert some_user is auth.login('some_user', 'some_password')


@with_setup(no_login)
def test_login_should_reset_session():
    auth.login('some_user', 'some_password')
    auth.cherrypy.session.regenerate.assert_called()


@with_setup(no_login)
def test_login_should_set_current_user():
    auth.login('some_user', 'some_password')
    assert some_user is auth.current_user()


@with_setup(logged_in)
def test_logout_should_unset_current_user():
    auth.logout()
    assert nobody is auth.current_user()


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


def test_require_should_decorate_with_cpconfig():
    condition = lambda: None
    condition2 = lambda: None
    some_object = lambda: None

    auth.require(condition)(some_object)
    auth.require(condition2)(some_object)

    eq_({'auth.require': [condition, condition2]},
        some_object._cp_config)


@with_setup(logged_in)
@patch('cherrymusicserver.auth.check')
def test_check_tool_should_test_conditions_from_cpconfig(checker):
    condition = Mock()
    auth.cherrypy.request.config = {'auth.require': [condition]}

    auth.check_tool()

    checker.assert_called_with(condition)


@with_setup(logged_in)
def test_check_tool_should_handle_no_requirements():
    auth.cherrypy.request.config = {'auth.require': None}
    auth.check_tool()


@with_setup(no_login)
def test_conditions_should_work_without_login():
    auth.is_admin()
    auth.is_user(None)()
    assert not auth.any()()
    assert auth.any(lambda: False, lambda: True)()


@with_setup(no_login)
def test_is_admin_should_reflect_current_user_admin_status():
    session_user('some_user')
    assert not auth.is_admin()

    session_user('admin')
    assert auth.is_admin()

    auth.logout()
    assert not auth.is_admin()


@with_setup(no_login)
def test_is_user_should_recognize_only_current_user():
    session_user('some_user')

    assert auth.is_user(mock_user_by_name('some_user'))()
    assert not auth.is_user(mock_user_by_name('admin'))()

    auth.logout()
    assert not auth.is_user(mock_user_by_name('some_user'))()


@with_setup(no_login)
def test_current_user_should_autologin_if_possible():
    with patch.dict(cherry.config, {'server.localhost_auto_login': True}):
        assert admin is auth.current_user()


@with_setup(no_login)
def test_login_should_reject_remote_admins_when_so_configured():

    init_request(ip='a.remote.ip')

    assert nobody is auth.login('admin', 'some_password')

    with patch.dict(cherry.config, {'server.permit_remote_admin_login': True}):
        assert admin is auth.login('admin', 'some_password')


@with_setup(no_login)
def test_current_user_survives_to_new_request():
    auth.login('some_user', 'some_password')
    init_request()
    assert some_user is auth.current_user()


#
#   HELPERS
#

def session_user(name):
    auth.logout()
    if name is not None:
        auth.login(name, 'some_password')

sessiondir = {}

def session_set(key, value):
    _log_op(key, '<--', value)
    sessiondir[key] = value
    _log_op(sessiondir)

def session_get(key):
    val = sessiondir[key]
    _log_op(key, '-->', val)
    return val

def session_del(key):
    del sessiondir[key]
    _log_op(key, '<-- DELETE')

usernames = ('nobody', 'admin', 'some_user',)


def mock_user(name, id):
    user = Mock(name=name)
    user.name = name
    user.is_valid = name in usernames[1:]
    user.isadmin = (name == 'admin')
    user.uid = id if user.is_valid else -1
    return user


users = dict((i, mock_user(name, i)) for i, name in enumerate(usernames))
nobody = users[0]
admin = users[1]
some_user = users[2]
users = defaultdict(lambda: nobody, users)


def mock_user_by_name(name):
    try:
        return users[usernames.index(name)]
    except:
        return nobody


def mock_user_by_id(id):
    return users[id]


def mock_user_auth(name, passw):
    if passw == 'some_password':
        return mock_user_by_name(name)
    return nobody

def _log_op(lval, op='', rval=''):
    log.d('{0} {1} {2}'.format(lval, op, rval).strip())
