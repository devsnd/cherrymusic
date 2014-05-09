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

from cherrymusicserver import service


class TestService(unittest.TestCase):

    def test_mutual_dependency(self):

        @service.user(myfoo='fooservice')
        class Reflecto(object):
            def __init__(self):
                service.provide('fooservice', self.__class__)
                assert self.myfoo

        self.assertRaises(service.MutualDependencyBreak, Reflecto)
