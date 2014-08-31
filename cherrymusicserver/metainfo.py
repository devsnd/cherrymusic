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

from cherrymusicserver import log
import sys, os

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

def getCueSongInfo(filepath, cue, track_n):
    info = cue.info[0]
    artist = info.performer or '-'
    album = info.title or '-'
    title = '-'
    track = cue.tracks[track_n-1]
    artist = track.performer or artist
    title = track.title or title
    if track_n < len(cue.tracks):
        track.nextstart = cue.get_next(track).get_start_time()
        audiolength = track.get_length()
    else:
        try:
            audiofilepath = os.path.join(os.path.dirname(filepath), info.file[0])
            tag = TinyTag.get(audiofilepath)
        except Exception:
            audiolength = None
            log.warn(_("Couldn't get length of '%s', setting 0"), audiofilepath)
        else:
            # XXX: TinyTag reports the wrong duration for some (FLAC) files, so do a sanity check.
            # XXX: This will fail if the reported length is longer than the start time of the last track.
            if tag.duration > 0 and track.get_start_time() < tag.duration:
                audiolength = tag.duration - track.get_start_time()
            else:
                audiolength = None
    return Metainfo(artist, album, title, track_n, audiolength)

def getSongInfo(filepath):
    ext = os.path.splitext(filepath)[1]
    try:
        tag = TinyTag.get(filepath)
    except LookupError:
        return Metainfo()
    # make sure everthing returned (except length) is a string
    for attribute in ['artist','album','title','track']:
        if getattr(tag, attribute) is None:
            setattr(tag, attribute, '')
    return Metainfo(tag.artist, tag.album, tag.title, str(tag.track), tag.duration)

