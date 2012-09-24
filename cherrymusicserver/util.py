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
from cherrymusicserver import log
from time import time

def configurationFile():
    return os.path.join(getConfigPath(), 'config')

def configurationFileExists():
    return os.path.exists(configurationFile())

def databaseFilePath(filename):
    configdir = os.path.join(getConfigPath(), 'db')
    if not os.path.exists(configdir):
        os.makedirs(configdir)
    configpath = os.path.join(configdir, filename)
    return configpath

def assureHomeFolderExists():
    dir = os.path.join(os.path.expanduser('~'), '.cherrymusic', 'db')
    if not os.path.exists(dir):
        os.makedirs(dir)

def getConfigPath():
    if len(sys.argv) > 2 and (sys.argv[1] == '-c' or sys.argv[1] == '--config-path') and os.path.exists(sys.argv[2]):
           return sys.argv[2]
    else:
        assureHomeFolderExists()
        return os.path.join(os.path.expanduser('~'), '.cherrymusic')

def readRes(path):
    return open(getResourcePath(path)).read()

def getResourcePath(path):
    #check share first
    resourceprefix = os.path.join(sys.prefix, 'share', 'cherrymusic')
    respath = os.path.join(resourceprefix, path)
    if not os.path.exists(respath):
        log.w("Couldn't find " + respath + ". Trying local install path.")
        #otherwise check local install
        resourceprefix = '.'
        respath = os.path.join(resourceprefix, path)
    if not os.path.exists(respath):
        log.w("Couldn't find " + respath + ". Trying home dir.")
        #lastly check homedir
        resourceprefix = os.path.join(os.path.expanduser('~'), '.cherrymusic')
        respath = os.path.join(resourceprefix, path)
    if not os.path.exists(respath):
        raise ResourceNotFound("Couldn't locate '" + path + "'!")
    return os.path.join(resourceprefix, path)

class ResourceNotFound(Exception):
       def __init__(self, msg):
           self.msg = msg
       def __str__(self):
           return repr(self.msg)

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


def phrase_to_lines(phrase, length=80):
    """splits a string along whitespace and distributes the parts into 
    lines of the given length"""
    words = phrase.split()
    lines = []
    line = ''
    for word in words:
        if len(line) + len(word) > length:
            lines.append(line)
            line = ''
        line += word + ' '
    lines.append(line)
    return lines



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

    def __init__(self, ticks, name=''):
        assert ticks > 0, "expected ticks must be > 0"
        self._ticks = 0
        self._expected_ticks = ticks
        self._starttime = time()
        self._finished = False
        self._finishtime = 0
        self.name = name

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
        self._finistime = time()

    def formatstr(self, fstr, *args):
        add = ''.join(list(args))
        fstr = fstr % {'eta': self.etastr,
                       'percent': self.percentstr,
                       'ticks': self._ticks,
                       'total': self._expected_ticks}
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
        reftime = self._finishtime if self._finished else time()
        return reftime - self.starttime

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


class ProgressTree(Progress):
    def __init__(self, name=None, finishcallback=None, callbacklevel= -1):
        super().__init__(ticks=1, name=name)
        self._finishcallback = finishcallback
        self._callbacklevel = callbacklevel
        self._parent = None
        self._active_children = set()
        self.root = self
        self.level = 0
        self.reporter = None

    def spawnchild(self, name=None):
        child = ProgressTree(name if not name is None else self.name)
        child._parent = self
        child.root = self.root
        child.level = self.level + 1
        self.extend()
        if self._callbacklevel > self.level:
            child._callbacklevel = self._callbacklevel
            child._finishcallback = self._finishcallback
        return child

    def extend(self, amount=1):
        assert amount > 0
        if self._finished:
            self.unfinish()
        self._expected_ticks += amount

    def unfinish(self):
        self._finished = False
        if not self._parent is None:
            self._parent._active_children.add(self)

    def _start(self):
        super()._start()
        if not self._parent is None:
            self._parent._active_children.add(self)

    def tick(self, report=True):
        super().tick()
        if report and self.root.reporter:
            self.root.reporter.tick(self)
        if self._ticks == self._expected_ticks:
            self.finish()

    def finish(self):
        if self._finished:
            return
        super().finish()
        if not self._parent is None:
            self._parent.tick(report=False)
            self._parent._active_children.remove(self)
        if self._finishcallback:
            self._finishcallback(self)

    @property
    def completeness(self):
        if self._finished:
            return 1.0
        c = self._ticks
        for child in self._active_children:
            c += child.completeness
        c /= self._expected_ticks
        return min(c, 1.0)

    @property
    def percent(self):
        return self.completeness * 100

    @property
    def eta(self):
        if self._finished:
            return 0
        c = self.completeness
        if c == 0:
            return 0
        return (1 - c) * self.runtime / c

class ProgressReporter(object):
    '''
    Customizable progress reporter. Can report on every object with the
    following attributes or properties: 
    
    name : str
        a descriptive name of this progress
        
    eta : float
        estimated time to completion in seconds. negative values mean overtime
        
    level : int >= 0
        for nested progress: the nesting depth, with 0 being top
        
    root : progress not None
        for nested progress: the origin (super parent) progress; can be == this
    '''
    @classmethod
    def timefmt(cls, eta):
        '''the default time format: [+-]hh:mm:ss'''
        overtime = '-'
        if eta < 0:
            eta = -eta
            overtime = '+'
        tmp = eta
        hh = tmp / 3600
        tmp %= 3600
        mm = tmp / 60
        tmp %= 60
        ss = tmp
        return '%(ot)s%(hh)02d:%(mm)02d:%(ss)02d' % {
                                                     'hh': hh,
                                                     'mm': mm,
                                                     'ss': ss,
                                                     'etas': eta,
                                                     'ot':overtime,
                                                     }

    def __init__(self, lvl= -1, dly=1, timefmt=None, namefmt=None, repf=None):
        '''
        Creates a progress reporter with the following customization options:
        
        lvl : int (default -1)
            The maximum level in the progress hierarchy that will be reported.
            When a report is triggered, it will contain all progress event 
            up to this level that have occurred since the last report.
            A negative value will only report the last unreported progress event
            with the highest available level.
            
        dly : float (default 1)
            The target delay between reports, in seconds. A negative value
            will report all progress events that conform to ``lvl`` as soon
            as they happen.
            
        timefmt : callable(float) -> str (default ProgressReport.timefmt)
            A function that turns the number for the estimated completion time
            into a string. That number is provided by ``progress.root.eta``.
            Per default, it interpreted as seconds until completion, with 
            negative values meaning overtime since estimated completion.
            
        namefmt : callable(str) -> str (default: no conversion)
            A function that converts the name given by ``progress.name`` into
            a more suitable format.
            
        repf : callable(dict) (default: log '%(eta) %(nam) (%(tix))' as info)
           Function callback to handle the actual reporting. The dict argument
           contains the following items::
               'eta': completion time as str,
               'nam': progress name,
               'tix': total number of ticks registered with this reporter,
               'progress': progress to report on, containing the raw data
        '''
        self._eta_adjuster = MovingAverage().feed
        self._eta_formatter = __class__.timefmt if timefmt is None else timefmt
        self._name_formatter = (lambda s: s) if namefmt is None else namefmt
        self._reportfunc = (lambda d: log.i('%(eta)s %(nam)s (%(tix)s)', d)) if repf is None else repf
        self._replevel = lvl
        self._repintvl = dly
        self._maxlevel = 0
        self._levelcache = {}
        self._ticks = 0
        self._lastreport = 0

    def tick(self, progress):
        '''
        Register a progress advance for progress, potentially triggering a
        report. A total of ticks will be kept.
        '''
        self._ticks += 1
        self._maxlevel = max(self._maxlevel, progress.level)
        self._levelcache[progress.level] = progress
        if time() - self._lastreport > self._repintvl:
            self.reportlast()

    def reportlast(self):
        '''
        Report progress events since the last report. 
        '''
        lvl = 0
        while lvl < self._maxlevel:
            if lvl in self._levelcache:
                p = self._levelcache.pop(lvl)
                self.report(p)
                if lvl >= self._replevel:
                    break
            lvl += 1

    def report(self, progress):
        '''Trigger a report for ``progress``'''
        self._lastreport = time()
        self._reportfunc({
              'eta': self._eta_formatter(self._eta_adjuster(progress.root.eta)),
              'nam': self._name_formatter(progress.name),
              'tix': self._ticks,
              'progress' : progress,
              })


from collections import deque
class MovingAverage(object):
    def __init__(self, size=10):
        assert size > 0
        self._values = deque((0 for i in range(size)))
        self._avg = 0

    @property
    def avg(self):
        return self._avg

    def feed(self, val):
        old = self._values.popleft()
        try:
            self._avg += (val - old) / len(self._values)
        except TypeError as tpe:
            self._values.appendleft(old)
            raise tpe
        self._values.append(val)
        return self._avg
