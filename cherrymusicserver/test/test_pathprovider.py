#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import nose

#from mock import *
from nose.tools import *

import os.path

from cherrymusicserver import log
log.setTest()

from cherrymusicserver import pathprovider

def test_absOrConfigPath():
    relpath = 'relpath'
    abspath = os.path.abspath(relpath)
    ok_(pathprovider.absOrConfigPath(relpath).startswith(pathprovider.getConfigPath()))
    eq_(abspath, pathprovider.absOrConfigPath(abspath))


def test_base64coding():
    """ base64encode and base64decode must satisfy `decode(encode(x)) == x` """
    from base64 import b64encode
    from functools import reduce
    from backport import unichr  # py2 compat

    # quick and dirty: list of strings that use whole base64 alphabet in utf-8
    teststrings = [unichr(i) for i in range(2**12)]

    # check if test set is complete
    b64test = (b64encode(c.encode('utf-8')) for c in teststrings)
    b64chars = reduce(set.union, b64test, set())
    eq_(65, len(b64chars), "Whole base64 alphabet must be used in test set")

    # check if encode and decode are inverse functions
    encode = pathprovider.base64encode
    decode = pathprovider.base64decode
    for expected in teststrings:
        transcoded = decode(encode(expected))
        eq_(expected, transcoded)


if __name__ == '__main__':
    nose.runmodule()
