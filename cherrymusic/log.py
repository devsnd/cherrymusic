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
import logging
import logging.config
import inspect
import os

from logging import NOTSET, DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL, FATAL


LOGLEVEL = "INFO"

CONFIG = {
"version": 1,
"formatters": {"brief": {"format": "[%(asctime)s] %(levelname)-8s: %(message)s",
                         "datefmt": "%y%m%d-%H:%M"},
                "full": {"format": "%(asctime)s %(name)-20s %(levelname)-8s\n"
                                   "from %(org_filename)s,line %(org_lineno)d"
                                   "\n%(message)s"}
                },
 "handlers": {"console": {
                   "class": "logging.StreamHandler",
                   "formatter": "brief",
                   "level": "DEBUG",
                   "stream": "ext://sys.stdout"},
              "console_priority": {
                   "class": "logging.StreamHandler",
                   "formatter": "brief",
                   "level": "ERROR",
                   "stream": "ext://sys.stderr"},
              "logfile_error": {
                    "class" : "logging.FileHandler",
                    "formatter": "full",
                    "level": "ERROR",
                    "filename": "error.log",
                    "encoding": "utf-8",
                    "delay": True,},
              },
 "loggers": {"test": {
                      "level": "WARN",
                      "propagate": False,
                      "handlers": ["console", ]
                      }
             },
 "root": {"level": LOGLEVEL,
          "handlers": ["console", "console_priority", "logfile_error"]}}

logging.config.dictConfig(CONFIG)

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
    _get_logger().warn(msg, *args, **kwargs)


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


def _get_logger():
    '''find out the caller's module name and get or create a corresponding
    logger. if caller has no module, return root logger.'''
    global __istest
    caller_frm = inspect.stack()[2]
    orgpath = caller_frm[1]
    orgfile = os.path.basename(orgpath)
    caller_info = {
                    'org_filename': orgfile,
                    'org_lineno': caller_frm[2],
                    'org_funcName': caller_frm[3],
                    'org_module': os.path.splitext(orgfile)[0],
                    'org_pathname': orgpath,
                   }
    caller_mod = inspect.getmodule(caller_frm[0])
    if __istest:
        name = 'test'
    else:
        name = None if caller_mod is None else caller_mod.__name__
    logger = logging.LoggerAdapter(logging.getLogger(name), caller_info)
    return logger



