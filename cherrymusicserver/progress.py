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

from time import time

from cherrymusicserver import log
from cherrymusicserver import util


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
        self._finishtime = time()

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
        hh, mm, ss = util.splittime(eta)
        return '%(ot)s%(hh)02d:%(mm)02d:%(ss)02d' % {
                                                     'hh': hh,
                                                     'mm': mm,
                                                     'ss': ss,
                                                     'ot':overtime,
                                                     }


class ProgressTree(Progress):
    '''
    Extension of the Progress concept that allows spawning 'child progress'
    objects that will contribute a tick to their parent on completion.
    '''

    def __init__(self, name=None, parent=None):
        super(self.__class__, self).__init__(ticks=1, name=name)
        self._parent = parent
        self._active_children = set()
        self.root = self
        self.level = 0
        self.reporter = None

    def __repr__(self):
        return '[%3d:%3d=%.2f] %d %.1f->[%s] %s' % (
                                      self._ticks,
                                      self._expected_ticks,
                                      self.completeness,
                                      len(self._active_children),
                                      self.runtime,
                                      self.etastr,
                                      self.name,
                                      )

    def spawnchild(self, name=None):
        '''Creates a child progress that will tick this progress on finish'''
        if name is None:
            name = self.name
        child = ProgressTree(name, parent=self)
        child.root = self.root
        child.level = self.level + 1
        self.extend()
        return child

    def extend(self, amount=1):
        '''Raises the number of expected ticks by amount'''
        assert amount > 0
        if self._finished:
            self.unfinish()
        self._expected_ticks += amount

    def unfinish(self):
        '''If progress resumes after a finish has been declared, undo the
        effects of finish().'''
        self._finished = False
        if not self._parent is None:
            self._parent.untick()
            self._parent._active_children.add(self)

    def untick(self):
        '''Take back a past tick'''
        if self._ticks > 0:
            if self._ticks == self._expected_ticks:
                self.unfinish()
            self._ticks -= 1

    def _start(self):
        super(self.__class__, self)._start()
        if not self._parent is None:
            self._parent._active_children.add(self)

    def tick(self, report=True):
        super(self.__class__, self).tick()
        if report and self.root.reporter:
            self.root.reporter.tick(self)
        if self._ticks == self._expected_ticks:
            self.finish()

    def finish(self):
        if self._finished:
            return
        super(self.__class__, self).finish()
        if not self._parent is None:
            self._parent.tick(report=False)
            self._parent._active_children.remove(self)

    @property
    def completeness(self):
        '''Ratio of registered ticks to total expected ticks. Can be > 1.'''
        if self._finished:
            return 1.0
        c = self._ticks
        for child in self._active_children:
            c += child.completeness
        c /= self._expected_ticks
        return c

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
        '''the default time format: [+]hh:mm:ss'''
        overtime = 'ETA '
        if eta < 0:
            eta = -eta
            overtime = '+'
        hh, mm, ss = util.splittime(eta)
        return '%(ot)s%(hh)02d:%(mm)02d:%(ss)02d' % {
                                                     'hh': hh,
                                                     'mm': mm,
                                                     'ss': ss,
                                                     'ot':overtime,
                                                     }

    @classmethod
    def prettytime(cls, eta):
        '''
        time display with variable precision: only show the most interesting
        time unit.
        '''
        def round_to(val, stepsize):
            return (val + stepsize / 2) // stepsize * stepsize

        prefix = 'ETA '
        if eta < 0:
            eta = -eta
            prefix = '+'
        hh, mm, ss = util.splittime(eta)
        if hh > 3:
            timestr = '%2d hrs' % hh
        elif hh > 0.25:
            hh = round_to(hh * 100, 25) / 100
            timestr = '%.2f h' % hh
        elif mm > 0.8:
            timestr = '%2d min' % int(mm + 0.5)
        elif ss > 20:
            timestr = '%2d sec' % round_to(ss, 20)
        elif ss > 5:
            timestr = '%2d sec' % round_to(ss, 5)
        else:
            timestr = '%2d sec' % ss
        return prefix + timestr


    @classmethod
    def prettyqty(cls, amount):
        '''return a quantity as kilos (k) or megas (M) if  justified)'''
        if amount < 10000:
            return '%d' % (amount,)
        if amount < 10e6:
            return '%dk' % (amount // 1000,)
        if amount < 10e7:
            return '%1.1fM' % (amount // 10e6,)
        return '%dM' % (amount // 10e6,)


    def __init__(self, lvl= -1, dly=1, timefmt=None, namefmt=None, repf=None):
        '''
        Creates a progress reporter with the following customization options:

        lvl : int (default -1)
            The maximum level in the progress hierarchy that will trigger a
            report. When a report is triggered, it will contain all progress
            events up to this level that have occurred since the last report. A
            negative value will use the time trigger (see ``dly``) to report the
            newest progress event with the upmost available level.

        dly : float (default 1)
            The target maximum delay between reports, in seconds. Triggers a
            report conforming with ``lvl`` if ``dly`` seconds have passed
            since the last report. Set to 0 to turn off timed reporting;
            set to a value < 0 for a time trigger without delay.

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
               'tix': str giving total ticks registered with this reporter,
               'progress': progress to report on, containing the raw data
        '''
        self._eta_adjuster = lambda e: e + 1
        self._eta_formatter = self.prettytime if timefmt is None else timefmt
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
        if progress.level <= self._replevel:
            self.report(progress)
            del self._levelcache[progress.level]
        elif self._repintvl and time() - self._lastreport > self._repintvl:
            self.reportlast()

    def reportlast(self):
        '''
        Report progress events since the last report.
        '''
        lvl = 0
        while lvl <= self._maxlevel:
            if lvl in self._levelcache:
                p = self._levelcache.pop(lvl)
                self.report(p)
                if lvl >= self._replevel:
                    break
            lvl += 1

    def report(self, progress):
        '''Trigger a report for ``progress``'''
        self._reportfunc({
              'eta': self._eta_formatter(self._eta_adjuster(progress.root.eta)),
              'nam': self._name_formatter(progress.name),
              'tix': self.prettyqty(self._ticks),
              'progress' : progress,
              })
        self._lastreport = time()
