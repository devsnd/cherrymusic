#!/usr/bin/env python3
# -*- coding: utf-8 -*- #
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2014 Tom Wallroth & Tilman Boerner
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
""" Things that are helpful when testing the CherryMusic backend """

import os
import shutil
import tempfile

from contextlib import contextmanager

from mock import *
from nose.tools import *

import cherrymusicserver

from cherrymusicserver import configuration
from cherrymusicserver import database
from cherrymusicserver import service

_default_config = configuration.from_defaults()     # load only once

@contextmanager
def cherryconfig(override=None):
    """ Context manager providing a CherryMusic default configuration
        that can be overridden.

        :param dict override: The overridden config values
    """
    override = override or {}
    config = cherrymusicserver.config or configuration.from_defaults()
    config = config.update(override)
    with patch('cherrymusicserver.config', config):
        yield config

@contextmanager
def tempdir(name_hint, keep=False):
    """ Context manager providing a temp directory to do stuff in.

        Yields the dir name. Deletes the directory on exit by default.

        :param str name_hint:  Part of the temp dir's name
        :param bool keep:   If true, don't delete the directory.
    """
    try:
        tmpdir = tempfile.mkdtemp(prefix=name_hint + '.')
        yield tmpdir
    finally:
        if not keep:
            shutil.rmtree(tmpdir, ignore_errors=False, onerror=None)


def mkpath(name, parent='.', content=''):
    """ Creates a file or subdir in directory ``parent``.

        If ``name.endswith('/')``, a directory is created, otherwise a file.
        ``content`` will be written to created files; specifying content
        when trying to create a directory will raise an AssertionError.
    """
    mkdir = name.endswith('/')
    name = name.rstrip('/')
    assert not (mkdir and content)
    abspath = os.path.abspath(os.path.join(parent, name))
    if mkdir:
        os.mkdir(abspath)
        assert os.path.isdir(abspath)
    else:
        with open(abspath, "w") as newfile:
            if content:
                newfile.write(content)
        assert os.path.isfile(abspath)
        if content:
            assert bool(os.path.getsize(abspath))
    return abspath


@contextmanager
def dbconnector(connector=None):
    """ Context manager providing a 'dbconnector' service

        :param database.AbstractConnector connector: Connector instance. MemConnector by default.
    """
    connector = connector or database.sql.MemConnector()
    real_get = service.get
    fake_get = lambda handle: connector if handle == 'dbconnector' else real_get(handle)
    with patch('cherrymusicserver.service.get', fake_get):
        yield connector
_dbconnector = dbconnector

def cherrytest(config=None, dbconnector=None):
    """ Function decorator that does some standard CherryMusic setup.

        It wraps the function call into a :func:`cherryconfig` and
        :func:`dbconnector` context.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with cherryconfig(config):
                with _dbconnector(dbconnector):
                    func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def symlinktest(func):
    ''' Decorator that returns a no-op function if symlinks are not supported '''
    if can_symlink():
        return func
    return lambda *a, **kw: None


def can_symlink():
    ''' Returns True if the OS environment allows symlinking '''
    global __can_symlink
    try:
        ok = __can_symlink
    except NameError:
        # actually try to symlink instead of ruling out entire OS families
        with tempdir('cherrymusic_symlinktest') as tmpd:
            try:
                os.symlink(tmpd, os.path.join(tmpd, 'symlink'))
            except (NameError, NotImplementedError, OSError):
                # Windows: older than Vista or no privileges to symlink
                # https://docs.python.org/3.2/library/os.html#os.symlink
                ok = __can_symlink = False
            else:
                ok = __can_symlink = True
    return ok

