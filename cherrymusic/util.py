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

import os
import sys
from cherrymusic import log

from time import time

def configurationFile():
    return os.path.join(getConfigPath(),'config')
    
def databaseFilePath(filename):
    configdir = os.path.join(getConfigPath(),'db')
    if not os.path.exists(configdir):
        os.makedirs(configdir)
    configpath = os.path.join(configdir,filename)
    return configpath
    
def assureHomeFolderExists():
    dir = os.path.join(os.path.expanduser('~'),'.cherrymusic','db')
    if not os.path.exists(dir):
        os.makedirs(dir)
        
def getConfigPath():
    if len(sys.argv)>2 and (sys.argv[1] == '-c' or sys.argv[1] == '--config-path') and os.path.exists(sys.argv[2]):
           return sys.argv[2]
    else:
        assureHomeFolderExists()
        return os.path.join(os.path.expanduser('~'),'.cherrymusic')
    

    

def filename(path, pathtofile=False):
    if pathtofile:
        return os.path.split(path)[0]
    else:
        return os.path.split(path)[1]

def stripext(filename):
    if '.' in filename:
        return filename[:filename.rindex('.')]
    return filename

def timed(func):
    """decorator to time function execution and log result on DEBUG"""
    from time import clock
    def wrapper(*args, **kwargs):
        starttime = clock()
        result = func(*args, **kwargs)
        duration = clock() - starttime
        log.d('%s.%s: %.4f', func.__module__, func.__name__, duration)
        return result
    return wrapper

def Property(func):
    """
    decorator that allows defining acessors in place as local functions.
    func must define fget, and may define fset, fdel and doc; `return locals()`
    at the end. 
    Seen at http://adam.gomaa.us/blog/2008/aug/11/the-python-property-builtin/
    """
    return property(**func())

class Progress(object):
    """Simple, timed progress tracking. 
    Based on the notion the time to complete a task can be broken up into 
    evenly spaced ticks, when a good estimate of total ticks
    is known. Estimates time remaining from the time taken for past ticks.
    The timer starts on the first tick."""

    def __init__(self, ticks):
        assert ticks > 0, "expected ticks must be > 0"
        self._ticks = 0
        self._expected_ticks = ticks
        self._starttime = time()
        self._finished = False

    def _start(self):
        self._starttime = time()

    def tick(self):
        """Register a tick with this object. The first tick starts the timer."""
        if self._ticks == 0:
            self._start()
        self._ticks += 1

    def finish(self):
        """Mark this progress as finished. Setting this is final."""
        self._finished = True

    def formatstr(self, fstr, *args):
        add = ''.join(list(args))
        fstr = fstr % {'eta': self.etastr, 'percent': self.percentstr, 'ticks': self._ticks, 'total': self._expected_ticks}
        return fstr + add

    @property
    def percent(self):
        """Number estimate of percent completed. Receiving more ticks than
        initial estimate increases this number beyond 100."""
        if (self._finished):
            return 100
        return self._ticks * 100 / self._expected_ticks

    @property
    def percentstr(self):
        """String version of `percent`. Invalid values outside of (0..100)
        are rendered as unknown value."""
        if (self._finished):
            return '100%'
        p = self.percent
        return '%s%%' % (str(int(p)) if p <= 100 else '??')

    @property
    def starttime(self):
        return self._starttime

    @property
    def runtime(self):
        if (self._ticks == 0):
            return 0
        return time() - self.starttime

    @property
    def eta(self):
        """Estimate of time remaining, in seconds. Ticks beyond initial estimate
        lead to a negative value."""
        if self._finished:
            return 0
        if self._ticks == 0:
            return 0
        return ((self._expected_ticks - self._ticks) * self.runtime / self._ticks) + 1

    @property
    def etastr(self):
        """String version of remaining time estimate. A negative `eta` is marked
        as positive overtime."""
        overtime = ''
        eta = self.eta
        if eta < 0:
            eta = -eta
            overtime = '+'
        tmp = eta
        hh = tmp / 3600
        tmp %= 3600
        mm = tmp / 60
        tmp %= 60
        ss = tmp
        return '%(ot)s%(hh)02d:%(mm)02d:%(ss)02d' % {'hh': hh, 'mm': mm, 'ss': ss, 'etas': eta, 'ot':overtime}
