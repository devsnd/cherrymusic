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

from cherrymusicserver import log
import sys

has_stagger = has_mutagen = has_audioread = False

#check for meta info libraries
if sys.version_info >= (3,):
    #stagger is only for python 3
    try:
        import stagger
        has_stagger = True
    except ImportError:
        log.w(_('''python library "stagger" not found: There will be no ID-tag support!'''))

else:
    try:
        import mutagen
        has_mutagen = True
    except ImportError:
        log.w(_('''python library "mutagen" not found: There will be no ID-tag support!'''))

try:
    import audioread
    has_audioread = True
except ImportError:
    log.w(_('''python library "audioread" not found!
    -Audio file length can't be determined without it!'''))

class Metainfo():
    def __init__(self, artist, album, title, track, length):
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
#
# Mock implementation for faild import (might be handy if
# multiple libs are used to determine metainfos)
#

#stagger

class MockTag():
    def __init__(self):
        self.artist = ''
        self.album = ''
        self.title = ''
        self.track = ''

def getSongInfo(filepath):
    if has_stagger:
        try:
            tag = stagger.read_tag(filepath)
        except Exception:
            tag = MockTag()
    elif has_mutagen:
        try:
            tag = MockTag()
            file_info = mutagen.File(filepath, easy=True)

            # NOTE: Joining in order to emulate stagger's formatting of
            #       multiple frames.
            tag.artist = " / ".join(file_info.get('artist', [tag.artist]))
            tag.album = " / ".join(file_info.get('album', [tag.album]))
            tag.title = " / ".join(file_info.get('title', [tag.title]))

            # NOTE: Splitting out the actual track number since mutagen returns
            #       a total as well.
            tag.track = file_info.get('tracknumber',
                                      [tag.track])[0].split('/')[0]
        except Exception:
            tag = MockTag()
    else:
        tag = MockTag()

    if has_audioread:
        try:
            with audioread.audio_open(filepath) as f:
                audiolength = f.duration
        except Exception as e:
            log.w("audioread fail: unable to fetch duration of %(file)r (%(exception)s)",
                {'file': filepath, 'exception': type(e).__name__})
            audiolength = 0
    else:
        audiolength = 0
    return Metainfo(tag.artist, tag.album, tag.title, tag.track, audiolength)
