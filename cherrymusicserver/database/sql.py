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
'''SQL Database handling.'''

import os.path
import sqlite3
import tempfile

from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver.database.connect import AbstractConnector, BoundConnector


@service.provider('dbconnector')
class SQLiteConnector(AbstractConnector):
    '''Connector for SQLite3 databases.

    By specification of the python sqlite3 module, sharing connections is to
    be considered NOT THREADSAFE.

    datadir: str
        Base directories of database files.
    suffix: str (optional)
        Suffix to append to database filenames.
    connargs: dict (optional)
        Dictionary with keyword args to pass on to sqlite3.Connection.
    '''
    def __init__(self, datadir='', suffix='', connargs={}):
        self.datadir = datadir
        self.suffix = suffix
        self.connargs = connargs

    def connection(self, dbname):
        return sqlite3.connect(self.dblocation(dbname), **self.connargs)

    def dblocation(self, basename):
        if self.suffix:
            basename = os.path.extsep.join((basename, self.suffix))
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

    _active_updaters = set()

    def __init__(self, name, dbdef):
        assert name and dbdef
        assert name not in self._active_updaters, (
            'there can be only one active updater per database (%r)' % (name,))
        self._active_updaters.add(name)
        self.name = name
        self.desc = dbdef
        self.db = BoundConnector(self.name)
        self._init_meta()

    def __del__(self):
        self._active_updaters.remove(self.name)

    def __repr__(self):
        return 'updater({0!r}, {1} -> {2})'.format(
            self.name,
            self._version,
            self._target,
        )

    @property
    def needed(self):
        """``True`` if the database version is less then the maximum defined."""
        version, target = self._version, self._target
        log.d('%s update check: version=[%s] target=[%s]', self.name, version, target)
        return version is None or version < target

    @property
    def requires_consent(self):
        """`True` if any missing updates require user consent."""
        for version in self._updates_due:
            if 'prompt' in self.desc[version]:
                return True
        return False

    @property
    def reasons(self):
        """ Return an iterable of strings giving the reasons for updates that
            require user consent.
        """
        for version in self._updates_due:
            if 'prompt' in self.desc[version]:
                yield self.desc[version]['prompt']

    def run(self):
        """Update database schema to the highest possible version."""
        log.i('%r: updating database schema', self.name)
        log.d('from version %r to %r', self._version, self._target)
        if None is self._version:
            self._init_with_version(self._target)
        else:
            for version in self._updates_due:
                self._update_to_version(version)

    def reset(self):
        """Delete all content from the database along with supporting structures."""
        version = self._version
        log.i('%s: resetting database', self.name)
        log.d('version: %s', version)
        if None is version:
            log.d('nothing to reset.')
            return
        with self.db.transaction() as txn:
            txn.isolation_level = 'EXCLUSIVE'
            txn.executescript(self.desc[version]['drop.sql'])
            txn.executescript(self._metatable['drop.sql'])
            txn.executescript(self._metatable['create.sql'])
            self._setversion(None, txn)

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
        with self.db.transaction() as txn:
            txn.isolation_level = "EXCLUSIVE"
            txn.executescript(self._metatable['create.sql'])
            if content and self._version is None:
                log.d('%s: unversioned content found: %r', self.name, content)
                self._setversion(0, txn)

    def _init_with_version(self, vnum):
        log.d('initializing database %r to version %d', self.name, vnum)
        with self.db.transaction() as txn:
            txn.isolation_level = "EXCLUSIVE"
            txn.executescript(self.desc[vnum]['create.sql'])
            self._setversion(vnum, txn)

    def _update_to_version(self, vnum):
        log.d('updating database %r to version %d', self.name, vnum)
        with self.db.transaction() as txn:
            txn.isolation_level = "EXCLUSIVE"
            txn.executescript(self.desc[vnum]['update.sql'])
            self._setversion(vnum, txn)


@service.provider('dbconnector')
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


@service.provider('dbconnector')
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
