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

import unittest

import audiotranscode as transcode

from cherrymusicserver import log
log.setTest()
    
class TestTranscode(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    @unittest.skipIf('mp3' not in transcode.Encoders.keys(),
                     'skip if missing optional dependency would cause an error')
    def test_mp3ToMp3(self):
        for data in transcode.getTranscoded('test.mp3','mp3',usetmpfile=False):
            continue


    @unittest.skipIf('ogg' not in transcode.Encoders.keys(),
                     'skip if missing optional dependency would cause an error')
    def test_mp3ToOgg(self):
        for data in transcode.getTranscoded('test.mp3','ogg',usetmpfile=False):
            continue


    @unittest.skipIf('aac' not in transcode.Encoders.keys(),
                     'skip if missing optional dependency would cause an error')
    def test_mp3ToAac(self):
        for data in transcode.getTranscoded('test.mp3','aac',usetmpfile=False):
            continue

if __name__ == "__main__":
    unittest.main()
