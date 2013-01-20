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
import base64
import codecs
from cherrymusicserver import log
from time import time

PERFORMANCE_TEST = True

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

def base64encode(s):
    return codecs.decode(base64.b64encode(codecs.encode(s,'UTF-8')),'UTF-8')
    
def base64decode(s):
    return codecs.decode(base64.b64decode(s),'UTF-8')

def assureHomeFolderExists(subfolder='db'):
    dirpath = os.path.join(os.path.expanduser('~'), '.cherrymusic', subfolder)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def getConfigPath():
    if len(sys.argv) > 2 and (sys.argv[1] == '-c' or sys.argv[1] == '--config-path') and os.path.exists(sys.argv[2]):
        return sys.argv[2]
    else:
        assureHomeFolderExists()
        return os.path.join(os.path.expanduser('~'), '.cherrymusic')

def readRes(path):
    with open(getResourcePath(path)) as f:
        return f.read()

def getResourcePath(path):
    #check share first
    resourceprefix = os.path.join(sys.prefix, 'share', 'cherrymusic')
    respath = os.path.join(resourceprefix, path)
    if not os.path.exists(respath):
        log.w("Couldn't find " + respath + ". Trying local install path.")
        #otherwise check local install
        resourceprefix = os.path.dirname(os.path.dirname(__file__))
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
    
    each paragraph is followed by a blank line, replacing all blank lines
    separating the paragraphs in the phrase; if paragraphs get squashed in your
    multiline strings, try inserting explicit newlines."""

    import re
    parag_ptn = r'''(?x)   # verbose mode  
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
    '''converts time given in seconds into a tuple: (hours, minutes, seconds)'''
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
            log.w('|   ' * (Performance.indentation - 1) + '/ˉˉ' + self.text)

    def __exit__(self, type, value, traceback):
        global PERFORMANCE_TEST
        if PERFORMANCE_TEST:
            duration = (time() - self.time) * 1000
            log.w('|   ' * (Performance.indentation - 1) + '\__ %g ms' % (duration,))
            Performance.indentation -= 1

def time2text(sec):
    abssec = abs(sec)
    minutes = abssec/60
    hours = minutes/60
    days = hours/24
    weeks = days/7
    months = days/30
    years = months/12
    if abssec > 30:
        if int(years) != 0:
            t = str(int(years))+' years'            
        elif int(months) != 0:
            t = str(int(months))+' months'
        elif int(weeks) != 0:
            t = str(int(weeks))+' weeks'
        elif int(days) != 0:
            t = str(int(days))+' days'
        elif int(hours) != 0:
            if int(hours) == 1:
                t = 'an hour'
            else:
                t = str(int(hours))+' hours'
        elif hours > 0.45:
            t = 'half an hour'
        elif int(minutes) != 0:
            if int(minutes) == 1:
                t = 'a minute'
            else:
                t = str(int(minutes))+' minutes'
        else:
            t = 'a few seconds'
        if sec > 0:
            t = t+' ago'
        else:
            t = 'in '+t
    else:
        t = 'just now'
    return t
