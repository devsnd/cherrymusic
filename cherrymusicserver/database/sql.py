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
'''SQL Database handling.'''

import os.path
import sqlite3
import tempfile
import threading

from cherrymusicserver import log
from cherrymusicserver.database.connect import AbstractConnector, BoundConnector


class SQLiteConnector(AbstractConnector):
    '''Connector for SQLite3 databases.

    By specification of the python sqlite3 module, sharing connections is to
    be considered NOT THREADSAFE.

    datadir: str
        Base directories of database files.
    extension: str (optional)
        Extension to append to database filenames.
    connargs: dict (optional)
        Dictionary with keyword args to pass on to sqlite3.Connection.
    '''
    def __init__(self, datadir='', extension='', connargs={}):
        self.datadir = datadir
        self.extension = extension
        self.connargs = connargs

    def connection(self, dbname):
        return sqlite3.connect(self.dblocation(dbname), **self.connargs)

    def dblocation(self, basename):
        if self.extension:
            basename = os.path.extsep.join((basename, self.extension))
        return os.path.join(self.datadir, basename)


class Updater(object):
    '''Handle the versioning needs of a single database.

    name : str
        The name of the database to manage.
    dbdef : dict
        The corresponding definition.
    connector : :class:`cherrymusicserver.database.connect.AbstractConnector`
        To connect to the database.
    '''

    _metatable = {
        'create.sql': """CREATE TABLE IF NOT EXISTS _meta_version(
                            version TEXT,
                            _created INTEGER NOT NULL DEFAULT (datetime('now'))
                        );""",
        'drop.sql': """DROP TABLE IF EXISTS _meta_version;"""
    }

    _classlock = threading.RLock()
    _dblockers = {}

    def __init__(self, name, dbdef):
        assert name and dbdef
        self.name = name
        self.desc = dbdef
        self.db = BoundConnector(self.name)
        with self:
            self._init_meta()

    def __del__(self):
        self._unlock()

    def __repr__(self):
        return 'updater({0!r}, {1} -> {2})'.format(
            self.name,
            self._version,
            self._target,
        )

    def __enter__(self):
        self._lock()
        return self

    def __exit__(self, exctype, exception, traceback):
        self._unlock()

    @property
    def _islocked(self):
        name, lockers = self.name, self._dblockers
        with self._classlock:
            return name in lockers and lockers[name] is self

    def _lock(self):
        name, lockers = self.name, self._dblockers
        with self._classlock:
            assert lockers.get(name, self) is self, (
                name + ': is locked by another updater')
            lockers[name] = self

    def _unlock(self):
        with self._classlock:
            if self._islocked:
                del self._dblockers[self.name]

    @property
    def needed(self):
        """ ``True`` if the database is unversioned or if its version is less
            then the maximum defined.
        """
        self._validate_locked()
        version, target = self._version, self._target
        log.d('%s update check: version=[%s] target=[%s]',
              self.name, version, target)
        return version is None or version < target

    @property
    def requires_consent(self):
        """`True` if any missing updates require user consent."""
        self._validate_locked()
        for version in self._updates_due:
            if 'prompt' in self.desc[version]:
                return True
        return False

    @property
    def prompts(self):
        """ Return an iterable of string prompts for updates that require user
            consent.
        """
        self._validate_locked()
        for version in self._updates_due:
            if 'prompt' in self.desc[version]:
                yield self.desc[version]['prompt']

    def run(self):
        """Update database schema to the highest possible version."""
        self._validate_locked()
        log.i('%r: updating database schema', self.name)
        log.d('from version %r to %r', self._version, self._target)
        if None is self._version:
            self._init_with_version(self._target)
        else:
            for version in self._updates_due:
                self._update_to_version(version)

    def reset(self):
        """Delete all content from the database along with supporting structures."""
        self._validate_locked()
        version = self._version
        log.i('%s: resetting database', self.name)
        log.d('version: %s', version)
        if None is version:
            log.d('nothing to reset.')
            return
        with self.db.connection() as cxn:
            cxn.executescript(self.desc[version]['drop.sql'])
            cxn.executescript(self._metatable['drop.sql'])
            cxn.executescript(self._metatable['create.sql'])
            self._setversion(None, cxn)
        cxn.close()

    def _validate_locked(self):
        assert self._islocked, 'must be called in updater context (use "with")'

    @property
    def _version(self):
        try:
            return self.__version
        except AttributeError:
            maxv = self.db.execute('SELECT MAX(version) FROM _meta_version').fetchone()
            maxv = maxv and maxv[0]
            self.__version = maxv if maxv is None else str(maxv)
            return self.__version

    def _setversion(self, value, conn=None):
        del self.__version
        conn = conn or self.db.connection
        log.d('{0}: set version to {1}'.format(self.name, value))
        conn.execute('INSERT INTO _meta_version(version) VALUES (?)', (value,))

    @property
    def _target(self):
        return max(self.desc)

    @property
    def _updates_due(self):
        if None is self._version:
            return ()
        versions = sorted(self.desc)
        start = versions.index(self._version) + 1
        return versions[start:]

    def _init_meta(self):
        content = self.db.execute('SELECT type, name FROM sqlite_master;').fetchall()
        content = [(t, n) for t, n in content if n != '_meta_version' and not n.startswith('sqlite')]
        with self.db.connection() as cxn:
            cxn.isolation_level = "EXCLUSIVE"
            cxn.executescript(self._metatable['create.sql'])
            if content and self._version is None:
                log.d('%s: unversioned content found: %r', self.name, content)
                self._setversion(0, cxn)
        cxn.isolation_level = ''
        cxn.close()

    def _init_with_version(self, vnum):
        log.d('initializing database %r to version %s', self.name, vnum)
        cxn = self.db.connection()
        cxn.isolation_level = None  # autocommit
        self._runscript(vnum, 'create.sql', cxn)
        self._run_afterscript_if_exists(vnum, cxn)
        self._setversion(vnum, cxn)
        cxn.isolation_level = ''
        cxn.close()

    def _update_to_version(self, vnum):
        log.d('updating database %r to version %d', self.name, vnum)
        cxn = self.db.connection()
        cxn.isolation_level = None  # autocommit
        self._runscript(vnum, 'update.sql', cxn)
        self._run_afterscript_if_exists(vnum, cxn)
        self._setversion(vnum, cxn)
        cxn.isolation_level = ''
        cxn.close()

    def _run_afterscript_if_exists(self, vnum, conn):
        try:
            self._runscript(vnum, 'after.sql', conn)
        except KeyError:
            pass

    def _runscript(self, version, name, cxn):
        try:
            cxn.executescript(self.desc[version][name])
        except sqlite3.OperationalError:
            # update scripts are tested, so the problem's seems to be sqlite
            # itself
            log.x(_('Exception while updating database schema.'))
            log.e(_('Database error. This is probably due to your version of'
                    ' sqlite being too old. Try updating sqlite3 and'
                    ' updating python. If the problem persists, you will need'
                    ' to delete the database at ' + self.db.dblocation))
            import sys
            sys.exit(1)

class TmpConnector(AbstractConnector):
    """Special SQLite Connector that uses its own temporary directory.

    As with the sqlite3 module in general, sharing connections is NOT THREADSAFE.
    """
    def __init__(self):
        self.testdirname = tempfile.mkdtemp(suffix=self.__class__.__name__)

    def __del__(self):
        import shutil
        shutil.rmtree(self.testdirname, ignore_errors=True)

    def connection(self, dbname):
        return sqlite3.connect(self.dblocation(dbname))

    def dblocation(self, basename):
        return os.path.join(self.testdirname, basename)


class MemConnector(AbstractConnector):  # NOT threadsafe
    """Special SQLite3 Connector that reuses THE SAME memory connection for
    each dbname. This connection is NOT CLOSABLE by normal means.
    Therefore, this class is NOT THREADSAFE.
    """
    def __init__(self):
        self.connections = {}
        self.Connection = type(
            self.__class__.__name__ + '.Connection',
            (sqlite3.Connection,),
            {'close': self.__disconnect})

    def __del__(self):
        self.__disconnect(seriously=True)

    def __repr__(self):
        return '{name} [{id}]'.format(
            name=self.__class__.__name__,
            id=hex(id(self))
        )

    def connection(self, dbname):
        return self.__connect(dbname)

    def dblocation(self, _):
        return ':memory:'

    def __connect(self, dbname):
        try:
            return self.connections[dbname]
        except KeyError:
            cxn = sqlite3.connect(':memory:', factory=self.Connection)
            return self.connections.setdefault(dbname, cxn)

    def __disconnect(self, seriously=False):
        if seriously:
            connections = dict(self.connections)
            self.connections.clear()
            for cxn in connections.values():
                super(cxn.__class__, cxn).close()
