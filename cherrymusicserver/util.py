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

#python 2.6+ backward compability
from __future__ import unicode_literals

import os
import sys
import base64
import codecs
from cherrymusicserver import log
from time import time

PERFORMANCE_TEST = True


def timed(func):
    """decorator to time function execution and log result on DEBUG"""
    def wrapper(*args, **kwargs):
        starttime = time()
        result = func(*args, **kwargs)
        duration = time() - starttime
        log.d('%s.%s: %.4f s', func.__module__, func.__name__, duration)
        return result
    return wrapper


def trim_to_maxlen(maxlen, s, insert=' ... '):
    '''no sanity check for maxlen and len(insert)'''
    if len(s) > maxlen:
        keep = maxlen - len(insert)
        left = keep // 2
        right = keep - left
        s = s[:left] + insert + s[-right:]
    return s


def phrase_to_lines(phrase, length=80):
    """splits a string along whitespace and distributes the parts into
    lines of the given length.

    each paragraph is followed by a blank line, replacing all blank
    lines separating the paragraphs in the phrase; if paragraphs get
    squashed in your multiline strings, try inserting explicit newlines.

    """

    import re
    parag_ptn = r'''(?x)      # verbose mode
    (?:                       # non-capturing group:
        [ \t\v\f\r]*          #    any non-breaking space
        \n                    #    linebreak
    ){2,}                     # at least two of these
    '''

    paragraphs = re.split(parag_ptn, phrase)
    lines = []
    for paragraph in paragraphs:
        if not paragraph:
            continue
        words = paragraph.split()
        line = ''
        for word in words:
            if len(line) + len(word) > length:
                lines.append(line.rstrip())
                line = ''
            line += word + ' '
        lines += [line.rstrip(), '']
    return lines


def splittime(seconds):
    '''converts time given in seconds into a tuple: (hours, mins, secs)'''
    tmp = seconds
    hh = tmp / 3600
    tmp %= 3600
    mm = tmp / 60
    tmp %= 60
    ss = tmp
    return (hh, mm, ss)


def Property(func):
    """
    decorator that allows defining acessors in place as local functions.
    func must define fget, and may define fset, fdel and doc; `return locals()`
    at the end.
    Seen at http://adam.gomaa.us/blog/2008/aug/11/the-python-property-builtin/
    """
    return property(**func())


from collections import deque
import math


class MovingAverage(object):
    def __init__(self, size=15, fill=0):
        assert size > 0
        self._values = deque((fill for i in range(size)))
        self._avg = fill
        self._size = size

    @property
    def avg(self):
        return self._avg

    @property
    def min(self):
        return min(self._values)

    @property
    def max(self):
        return max(self._values)

    @property
    def median(self):
        sort = sorted(self._values)
        mid = self._size // 2
        median = sort[mid]
        if self._size % 2:
            return median
        return (median + sort[mid - 1]) / 2

    @property
    def variance(self):
        diff = []
        mean = self.avg
        [diff.append((x - mean) * (x - mean)) for x in self._values]
        return sum(diff) / len(diff)

    @property
    def stddev(self):
        return math.sqrt(self.variance)

    def feed(self, val):
        '''insert a new value and get back the new average'''
        old = self._values.popleft()
        try:
            self._avg += (val - old) / self._size
        except TypeError as tpe:
            self._values.appendleft(old)
            raise tpe
        self._values.append(val)
        return self._avg


class Performance:
    indentation = 0

    def __init__(self, text):
        self.text = text

    def __enter__(self):
        global PERFORMANCE_TEST
        if PERFORMANCE_TEST:
            self.time = time()
            Performance.indentation += 1
            log.w('|   ' * (Performance.indentation - 1)
                  + '/ˉˉ' + self.text)
            return self

    def __exit__(self, type, value, traceback):
        global PERFORMANCE_TEST
        if PERFORMANCE_TEST:
            duration = (time() - self.time) * 1000
            log.w('|   ' * (Performance.indentation-1)
                  + '\__ %g ms' % (duration,))
            Performance.indentation -= 1

    def log(self, text):
        global PERFORMANCE_TEST
        if PERFORMANCE_TEST:
            for line in text.split('\n'):
                log.w('|   ' * (Performance.indentation) + line)


def time2text(sec):
    abssec = abs(sec)
    minutes = abssec/60
    hours = minutes/60
    days = hours/24
    weeks = days/7
    months = days/30
    years = months/12
    if abssec > 30:
        if sec > 0:
            if int(years) != 0:
                if years > 1:
                    return _('%d years ago') % years
                else:
                    return _('a year ago')
            elif int(months) != 0:
                if months > 1:
                    return _('%d months ago') % months
                else:
                    return _('a month ago')
            elif int(weeks) != 0:
                if weeks > 1:
                    return _('%d weeks ago') % weeks
                else:
                    return _('a week ago')
            elif int(days) != 0:
                if days > 1:
                    return _('%d days ago') % days
                else:
                    return _('a day ago')
            elif int(hours) != 0:
                if hours > 1:
                    return _('%d hours ago') % hours
                else:
                    return _('an hour ago')
            elif hours > 0.45:
                return _('half an hour ago')
            elif int(minutes) != 0:
                if minutes > 1:
                    return _('%d minutes ago') % hours
                else:
                    return _('a minute ago')
            else:
                return _('a few seconds ago')
        else:
            if int(years) != 0:
                if years > 1:
                    return _('in %d years') % years
                else:
                    return _('in a year')
            elif int(months) != 0:
                if months > 1:
                    return _('in %d months') % months
                else:
                    return _('in a month')
            elif int(weeks) != 0:
                if weeks > 1:
                    return _('in %d weeks') % weeks
                else:
                    return _('in a week')
            elif int(days) != 0:
                if days > 1:
                    return _('in %d days') % days
                else:
                    return _('in a day')
            elif int(hours) != 0:
                if hours > 1:
                    return _('in %d hours') % hours
                else:
                    return _('in an hour')
            elif hours > 0.45:
                return _('in half an hour')
            elif int(minutes) != 0:
                if minutes > 1:
                    return _('in %d minutes') % hours
                else:
                    return _('in a minute')
            else:
                return _('in a few seconds')
    else:
        return _('just now')


class MemoryZipFile(object):

    def __init__(self):
        from io import BytesIO
        from zipfile import ZipFile
        self.buffer = BytesIO()
        self.zip = ZipFile(self.buffer, 'w')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def writestr(self, name, bytes):
        try:
            self.zip.writestr(name, bytes)
        except:
            log.x(_('Error writing file %(name)r to memory zip'), {'name': name})
            raise

    def getbytes(self):
        return self.buffer.getvalue()

    def close(self):
        self.zip.close()
