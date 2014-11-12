#!/usr/bin/env python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
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
import unittest

from cherrymusicserver import log
log.setTest()

from cherrymusicserver import database
from cherrymusicserver import service
from cherrymusicserver import userdb
from cherrymusicserver.database.sql import MemConnector, TmpConnector


class TestAuthenticate(unittest.TestCase):
    '''test authentication functions of userdb'''

    def setUp(self, dbconnector=MemConnector):
        service.provide('dbconnector', dbconnector)
        database.ensure_current_version(userdb.DBNAME)
        self.users = userdb.UserDB()
        self.users.addUser('user', 'password', False)

        #unittest2 compability
        if not hasattr(self,'assertTupleEqual'):
            def assertTupEq(t1,t2,msg):
                if not all(i==j for i,j in zip(t1,t2)):
                    raise AssertionError(msg)
            self.assertTupleEqual = assertTupEq
        #end of workaround


    def tearDown(self):
        pass

    def testRegisteredUserCanLogin(self):
        '''successful authentication must return authenticated user'''

        authuser = self.users.auth('user', 'password')

        self.assertEqual('user', authuser.name,
                         'authentication must return authenticated user')


    def testNoLoginWithWrongPassword(self):
        '''valid username and invalid password = authentication failure'''

        authuser = self.users.auth('user', 'passwordtypo')

        self.assertTupleEqual(userdb.User.nobody(), authuser,
                         'authentication failure must return invalid user')


    def testNoLoginWithInvalidUser(self):
        '''invalid username = authentication failure'''

        authuser = self.users.auth('!@#$%^&*(', ')(*&^%$#')

        self.assertTupleEqual(userdb.User.nobody(), authuser,
                         'authentication failure must return invalid user')

    def testChangePassword(self):
        connector = TmpConnector()     # use different connections, don't share
        self.setUp(connector)
        #create new user
        self.users.addUser('newpwuser', 'password', False)
        msg = self.users.changePassword('newpwuser', 'newpassword')
        self.assertEqual(msg, "success")

        authuser = self.users.auth('newpwuser', 'password')
        self.assertTupleEqual(userdb.User.nobody(), authuser,
                         'authentication with old password after change must fail')

        self.users = userdb.UserDB()    # force different DB connection
        authuser = self.users.auth('newpwuser', 'newpassword')
        self.assertEqual('newpwuser', authuser.name,
                         'authentication with new password failed')



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
