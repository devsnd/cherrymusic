# Python cuesheet parsing
# Copyright (C) 2009-2014  Jon Bergli Heier

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

import re

cdtext_re = {
    'REM': r'^(REM) (.+)$',
    'PERFORMER': r'^(PERFORMER) "?(.+?)"?$',
    'TITLE': r'^(TITLE) "?(.+?)"?$',
    #'FILE': r'^(FILE) "?(.+?)"? (BINARY|MOTOROLA|AIFF|WAVE|MP3)$',
    # XXX: The above line is the only correct one according to the spec, but some people
    #      seem to think that putting stuff like FLAC here instead is a good idea.
    'FILE': r'^(FILE) "?(.+?)"? (\w+)$',
    'TRACK': r'^(TRACK) (\d+) (AUDIO|CDG|MODE1/2048|MODE1/2352|MODE2/2336|MODE2/2352|CDI/2336|CDI2352)$',
    'INDEX': r'^(INDEX) (\d+) (\d+):(\d+):(\d+)$',
    'FLAGS': r'^((?:DCP|4CH|PRE|SCMS) ?){1,4}$',
    'ISRC': r'^(ISRC) (\w{5}\d{7})$',
    'SONGWRITER': r'^(SONGWRITER) "?(.+?)"?$',
    'CATALOG': r'^(CATALOG) (\d{13})$',
}

for k, v in cdtext_re.items():
    cdtext_re[k] = re.compile(v)

class CDText(object):
    def __init__(self, str):
        name = str.split()[0]
        self.re = cdtext_re[name]
        l = self.parse(str)
        self.type, self.value = l[0], l[1:]
        if type(self.value) == tuple and len(self.value) == 1:
            self.value = self.value[0]

    def __repr__(self):
        return '<CDText "%s" "%s">' % (self.type, self.value)

    def __str__(self):
        return repr(self)

    def parse(self, str):
        r = self.re.match(str)
        if not r:
            return None, None
        return r.groups()

class FieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        def find(name):
            for l in instance.cdtext:
                if l.type == name:
                    return l
        cdtext = find(self.field)
        return cdtext.value if cdtext else None

class Track(object):
    def __init__(self):
        self.cdtext = []
        self.abs_tot, self.abs_end, self.nextstart = 0, 0, None

    def add(self, cdtext):
        self.cdtext.append(cdtext)

    def set_abs_tot(self, tot):
        self.abs_tot = tot

    def set_abs_end(self, end):
        self.abs_end

    def get_start_time(self):
        index = self.index
        return int(index[1])*60 + int(index[2]) + float(index[3])/75

    def get_length(self):
        return self.nextstart - self.get_start_time()

for f in cdtext_re.keys():
    setattr(Track, f.lower(), FieldDescriptor(f))

class Cuesheet(object):
    def __init__(self, filename = None, fileobj = None):
        if not fileobj and filename:
            fileobj = open(filename, 'rb')
        if fileobj:
            self.parse(fileobj)

    def parse(self, f):
        info = []
        tracks = []
        track = Track()
        info.append(track)
        if not f.read(3) == b'\xef\xbb\xbf':
            f.seek(0)
        for line in f:
            line = line.strip()
            line = line.decode('utf-8')
            if not len(line):
                continue
            cdtext = CDText(line)
            if cdtext.type == 'TRACK':
                track = Track()
                tracks.append(track)
            track.add(cdtext)
        self.info = info
        self.tracks = tracks

    def get_next(self, track):
        found = False
        for i in self.tracks:
            if found:
                return i
            elif i == track:
                found = True
        return None
