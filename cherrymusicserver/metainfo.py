#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
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

from tinytag import TinyTag

class Metainfo():
    def __init__(self, artist='', album='', title='', track='', length=0):
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

def getSongInfo(filepath):
    try:
        tag = TinyTag.get(filepath)
    except LookupError:
        return Metainfo()
    # make sure everthing returned (except length) is a string
    for attribute in ['artist','album','title','track']:
        if getattr(tag, attribute) is None:
            setattr(tag, attribute, '')
    return Metainfo(tag.artist, tag.album, tag.title, str(tag.track), tag.duration)

