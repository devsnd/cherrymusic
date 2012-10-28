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

from cherrymusicserver import log

#set to True if any metainfo lib is available
metainfo_support = False
supported_file_formats = ('mp3')

#check for meta info libraries
try:
    import stagger
    has_stagger = True
    metainfo_support = True
except ImportError:
    log.w('''python library "stagger" not found!
-There will be no ID-tag support!''')
    has_stagger = False

try:
    import audioread
    has_audioread = True
except ImportError:
    log.w('''python library "audioread" not found!
-Audio file length can't be determined without it!''')
    has_audioread = False
    
class Metainfo():
    def __init__(self, artist='-', album='-', title='-', track='-', length=0):
        self.artist = artist
        self.album = album
        self.title = title
        self.track = track
        self.length = length
    def dict(self):
        return {
        'artist': self.artist,
        'album': self.album,
        'title': self.title,
        'track': self.track,
        'length': self.length
        }
    def getWordSet(self):
        words = []
        if self.artist != '-':
            words.append(self.artist)
        if self.album != '-':
            words.append(self.album)
        if self.title != '-':
            words.append(self.title)
        return words
#
# Mock implementation for faild import (might be handy if
# multiple libs are used to determine metainfos)
#

#stagger
        
class MockTag():
    def __init__(self):
        self.artist = '-'
        self.album = '-'
        self.title = '-'
        self.track = '-'
       
def getSongInfo(filepath):
<<<<<<< Updated upstream
    if filepath.endswith(supported_file_formats):
=======
    if filepath.lower().endswith(supported_file_formats):
>>>>>>> Stashed changes
        if has_stagger:
            try:
                tag = stagger.read_tag(filepath)
            except Exception:
                tag = MockTag()
        else:
            tag = MockTag()
                
        if has_audioread:
            try:
                with audioread.audio_open(filepath) as f:
                    audiolength = f.duration
            except Exception:
                log.e('audioread failed!')
                audiolength = 0
        else:
            audiolength = 0
        return Metainfo(tag.artist, tag.album, tag.title, tag.track, audiolength)
    return Metainfo()

    