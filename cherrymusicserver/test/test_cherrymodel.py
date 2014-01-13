#!/usr/bin/python3
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

from mock import *
from nose.tools import *

from collections import defaultdict

from cherrymusicserver import log
log.setTest()

from cherrymusicserver import cherrymodel

def cherryconfig(cfg=None):
    from cherrymusicserver import configuration
    cfg = cfg or {}
    c = configuration.from_defaults()
    c = c.update({'media.basedir': '/'})
    c = c.update(cfg)
    return c

@patch('cherrymusicserver.cherrymodel.cherry.config', cherryconfig())
@patch('cherrymusicserver.cherrymodel.os')
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.isplayable', lambda _: True)
def test_hidden_names_listdir(cache, os):
    model = cherrymodel.CherryModel()
    os.path.join = lambda *a: '/'.join(a)

    content = ['.hidden']
    cache.listdir.return_value = content
    os.listdir.return_value = content
    assert not model.listdir('')

    content = ['not_hidden.mp3']
    cache.listdir.return_value = content
    os.listdir.return_value = content
    assert model.listdir('')


@patch('cherrymusicserver.cherrymodel.cherry.config', cherryconfig({'search.maxresults': 10}))
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.cherrypy')
def test_hidden_names_search(cherrypy, cache):
    model = cherrymodel.CherryModel()

    cache.searchfor.return_value = [cherrymodel.MusicEntry('.hidden', dir=True)]
    assert not model.search('something')

    cache.searchfor.return_value = [cherrymodel.MusicEntry('nothidden', dir=True)]
    assert model.search('something')


if __name__ == '__main__':
    nose.runmodule()
