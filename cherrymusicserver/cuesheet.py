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
################################################################################
# 
# Roughly based on the code by Jon Bergli Heier (https://github.com/sn4kebite)
#
################################################################################

import re
import itertools
import codecs
from functools import partial

class CueSheetCommon(object):
    # we only support audio cuesheets
    TRACK_REGEX = re.compile('TRACK (\d+) AUDIO$')
    def __init__(self):
        self.title = None
        self.performer = None
        self.songwriter = None
        # commands are a set of tuples containing a regex and a function that
        # should be called if the regex matches. The function will receive the
        # first group of the matched regex
        self.commands = [
            (re.compile('TITLE "?(.+?)"?$'), partial(setattr, self, 'title')),
            (re.compile('PERFORMER "?(.+?)"?$'), partial(setattr, self, 'performer')),
            (re.compile('SONGWRITER "?(.+?)"?$'), partial(setattr, self, 'songwriter')),
        ]

    def parse(self, line):
        for regex, matchfunc in self.commands:
            match = regex.match(line)
            if match:
                matchfunc(match.group(1))
                return True
        return False

    def timecode_to_seconds(self, timecode):
        minutes, seconds, frames = timecode.split(':')
        # cds have 75 framesper second of audio
        return int(minutes)*60 + int(seconds) + int(frames)/75.0

class Track(CueSheetCommon):
    def __init__(self, filename, trackno):
        super().__init__()
        self.filename = filename
        self.trackno = trackno
        self.start_time_abs_sec = 0
        self.duration_sec = 0
        self.isrc = None
        self.flags = None  # subcode flags, see: https://en.wikipedia.org/wiki/Compact_Disc_subcode
        self.cdtext = []
        track_commands = [
            (re.compile('INDEX (\d+ \d+:\d+:\d+)$'), self.parse_index),
            (re.compile('ISRC (\w{5}\d{7})$'), partial(setattr, self, 'isrc')),
            # PREGAP 00:02:00  # etc etc
        ]
        for command in track_commands:
            self.commands.append(track_commands)

    def parse_index(self, regexgroup):
        trackno, timecode = regexgroup.split(' ')
        self.trackno = trackno
        self.start_time_abs_sec = self.timecode_to_seconds(timecode)

    def parse(self, lines):
        for line in lines:
            if CueSheetCommon.TRACK_REGEX.match(line):
                # found next track, stop parsing here.
                break
            else:
                super().parse(line)

class CueSheet(CueSheetCommon):
    def __init__(self, filename = None, fileobj = None):
        super().__init__()
        self.catalog = None
        self.rem = {}
        self.cdtextfile = None
        self.tracks = []
        self.files = []
        cuesheet_commands = [
            (re.compile('REM (.+)$'), self.add_comment),
            (re.compile('FILE "?(.+?)"? \w+$'), self.files.append),
            (re.compile('CATALOG (\d{13})$'), partial(setattr, self, 'catalog')),
        ]
        for command in cuesheet_commands:
            self.commands.append(command)
        if not fileobj and filename:
            fileobj = open(filename, 'rb')
        if fileobj:
            self.parse_cuesheet(fileobj)

    def add_comment(self, regexgroup):
        parts = regexgroup.split()
        self.rem[parts[0]] = ' '.join(parts[1:])

    def parse_cuesheet(self, fh):
        current_file = None
        utf8_bom = fh.read(3)
        if not utf8_bom == b'\xef\xbb\xbf':
            fh.seek(0)  # no bom, so rewind to start
        # strip all lines and remove empty lines, also utf-8 decode
        lines = [codecs.decode(line.strip(), 'utf-8')
                    for line in fh.readlines() if line.strip()]
        for lineno, line in enumerate(lines):
            matched = self.parse(line)
            if not matched:
                match_track = CueSheetCommon.TRACK_REGEX.match(line)
                if match_track:
                    trackno = match_track.group(1)
                    track = Track(self.files[-1], trackno)
                    remaining_lines = itertools.islice(lines, lineno, None)
                    track.parse(remaining_lines)
                    self.tracks.append(track)
        # set track durations from the start time of the next track
        for idx, this_track in enumerate(self.tracks):
            if idx+1 < len(self.tracks):
                next_track = self.tracks[idx+1]
                track.duration = next_track.start_time_abs_sec - this_track.start_time_abs_sec