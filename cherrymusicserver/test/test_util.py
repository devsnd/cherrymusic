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

from nose.tools import *

from cherrymusicserver import util
from cherrymusicserver import log
log.setTest()

def test_maxlen_trim():
    assert util.trim_to_maxlen(7, 'abcdefghi') == 'a ... i'

def test_phrase_to_lines():
    phrase = '''qwertyui9o0 sdfghjk dfghjk dfghj fghjk dfghjk fghj fghj
    ghjfdkj ahg jkdgf sjkdfhg skjfhg sjkfh sjkd fhgsjd hgf sdjhgf skjg
    fg hjkfghjk fghjk gfhjk fghj fghjk ghj fghj gfhjk fghj ghj

    asd'''
    lines = util.phrase_to_lines(phrase, length=80)
    assert 60 < len(lines[0]) < 80
    assert 60 < len(lines[1]) < 80
    assert len(lines[1]) < 80

def test_moving_average():
    mov = util.MovingAverage(size=2)
    assert mov.avg == 0
    assert mov.min == 0
    assert mov.max == 0
    mov.feed(2)
    assert mov.avg == 1
    assert mov.min == 0
    assert mov.max == 2

def test_time2text():
    assert util.time2text(0) == 'just now'
    for mult in [60, 60*60, 60*60*24, 60*60*24*31, 60*60*24*365]:
        for i in [-1, -3, 1, 3]:
            assert util.time2text(i * mult)

def test_performance_logger():
    with util.Performance('potato head') as p:
        p.log('elephant')

if __name__ == '__main__':
    nose.runmodule()
