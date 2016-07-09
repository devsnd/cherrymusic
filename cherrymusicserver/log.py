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

# pylint: disable=W0611
from backport import logging
import logging.config
import inspect
import os
import sys

from cherrymusicserver import pathprovider

from logging import NOTSET, DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL, FATAL


LOGLEVEL = INFO

class RelocateLoggingCall(logging.Filter):
    '''using this module's logging methods puts some misleading values into
    standard log record attributes, especially pertaining to the origin of
    the logging call. this filter corrects them with the help of
    extended attributes added by _get_logger()'''
    def filter(self, record):
        has_org = lambda seq: False if not seq else True if seq[0].startswith('org_') else has_org(seq[1:])
        if has_org(dir(record)):
            record.lineno = record.org_lineno
            record.funcName = record.org_funcName
            record.pathname = record.org_pathname
        return 1
relocator = RelocateLoggingCall()

class LowPass(logging.Filter):
    def __init__(self, cutoff):
        self.cutoff = cutoff

    def filter(self, record):
        return 1 if record.levelno < self.cutoff else 0


formatter_briefest = logging.Formatter(fmt='[%(asctime)s] %(message)s', datefmt='%y%m%d-%H:%M')
formatter_brief = logging.Formatter(fmt='[%(asctime)s] %(levelname)-8s: %(message)s', datefmt='%y%m%d-%H:%M')
formatter_full = logging.Formatter(fmt=('-'*80)+ '\n%(levelname)-8s [%(asctime)s] : %(name)-20s : from line (%(lineno)d) at\n\t%(pathname)s\n\t--\n\t%(message)s\n')

handler_console = logging.StreamHandler(stream=sys.stdout)

handler_console.formatter = formatter_briefest
handler_console.level = DEBUG
handler_console.addFilter(LowPass(WARNING))
handler_console.addFilter(relocator)

handler_console_priority = logging.StreamHandler(stream=sys.stderr)
handler_console_priority.formatter = formatter_brief
handler_console_priority.level = WARNING
handler_console_priority.addFilter(relocator)

handler_file_error = logging.FileHandler(os.path.join(pathprovider.getUserDataPath(), 'error.log'), mode='a', delay=True)
handler_file_error.formatter = formatter_full
handler_file_error.level = ERROR
handler_file_error.addFilter(relocator)

logging.root.setLevel(LOGLEVEL)
logging.root.addHandler(handler_console)
logging.root.addHandler(handler_console_priority)
logging.root.addHandler(handler_file_error)

testlogger = logging.getLogger('test')
testlogger.setLevel(CRITICAL)
testlogger.addHandler(handler_console)
testlogger.addHandler(handler_console_priority)
testlogger.propagate = False

logging.getLogger('cherrypy.error').setLevel(WARNING)




def debug(msg, *args, **kwargs):
    '''logs a message with severity DEBUG on the caller's module logger.
    uses the root logger if caller has no module.'''
    _get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    '''logs a message with severity INFO on the caller's module logger.
    uses the root logger if caller has no module.'''
    _get_logger().info(msg, *args, **kwargs)


def warn(msg, *args, **kwargs):
    '''logs a message with severity WARN on the caller's module logger.
    uses the root logger if caller has no module.'''
    _get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    '''logs a message with severity ERROR on the caller's module logger.
    uses the root logger if caller has no module.'''
    _get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    '''logs a message with severity CRITICAL on the caller's module logger.
    uses the root logger if caller has no module.'''
    _get_logger().critical(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    '''logs a message with severity ERROR on the caller's module logger,
    including exception information. uses the root logger if caller
    has no module.'''
    _get_logger().exception(msg, *args, **kwargs)

def level(lvl):
    '''sets the level for the caller's module logger, or, if there is no
    module, the root logger. `lvl` is an int as defined in logging, or
    a corresponding string respresentation.'''
    _get_logger().setLevel(lvl)


__istest = False
def setTest(state=True):
    global __istest
    __istest = state


d = debug
i = info
w = warn
e = error
c = critical
ex = exception
x = exception

warning = warn


def _get_logger():
    '''find out the caller's module name and get or create a corresponding
    logger. if caller has no module, return root logger.'''
    if __istest:
        return testlogger
    caller_frm = inspect.stack()[2]
    caller_mod = inspect.getmodule(caller_frm[0])
    name = None if caller_mod is None else caller_mod.__name__
    orgpath = caller_frm[1]
    orgfile = os.path.basename(orgpath)
    caller_info = {
                    'org_filename': orgfile,
                    'org_lineno': caller_frm[2],
                    'org_funcName': caller_frm[3],
                    #'org_module': name if name else os.path.splitext(orgfile)[0],
                    'org_pathname': orgpath,
                   }
    logger = logging.LoggerAdapter(logging.getLogger(name), caller_info)
    return logger



