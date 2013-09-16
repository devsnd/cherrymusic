#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
'''
Connect to databases.
'''

# from abc import ABCMeta, abstractmethod   # don't, for py2 compatibility

from cherrymusicserver import log

import cherrymusicserver.service as service


# class AbstractConnector(metaclass=ABCMeta):
class AbstractConnector(object):
    '''Provide database connections by name.

    Override :meth:`connection` and :meth:`dbname` to subclass.
    '''
    def __repr__(self):
        return self.__class__.__name__

    # @abstractmethod
    def connection(self, dbname):
        '''Return a connection object to talk to a database.'''
        raise NotImplementedError('abstract method')

    # @abstractmethod
    def dblocation(self, basename):
        '''Return the internal handle used for the database with ``basename``.'''
        raise NotImplementedError('abstract method')

    def bound(self, dbname):
        '''Return a :class:`BoundConnector` bound to the database with ``dbname``.'''
        return BoundConnector(dbname, self)

from contextlib import contextmanager

@service.user(baseconnector='dbconnector')
class BoundConnector(object):
    '''Provide connections to a specific database name.'''
    def __init__(self, dbname, overrideconnector=None):
        self.name = dbname
        if overrideconnector is not None:
            self.baseconnector = overrideconnector

    def __repr__(self):
        return '{cls}({0!r}, {1})'.format(
            self.name, repr(self.baseconnector),
            cls=self.__class__.__name__)

    @property
    def dblocation(self):
        '''Return the internal handle used for the bound database.'''
        return self.baseconnector.dblocation(self.name)

    def connection(self):
        '''Return a connection object to talk to the bound database.'''
        return self.baseconnector.connection(self.name)

    def execute(self, query, params=()):
        '''Connect to the bound database and execute a query; then return the
        cursor object used.'''
        cursor = self.connection().cursor()
        cursor.execute(query, params)
        return cursor

    @contextmanager
    def transaction(self, comment=None):
        ''' Context manager that commits or rolls back on exit, depending
            on exception status. Transactions will nest for the same
            BoundConnector object and only act when the top level transaction
            is exited. Nested transactions share the same connection.
        '''
        txn = _Transaction(self, comment)
        with txn as cursor:
            yield cursor


import threading

class ThreadlocalConnector(BoundConnector):
    ''' A BoundConnector that always returns the same connection from inside
        the same thread.'''

    def __init__(self, target, overrideconnector=None):
        ''' target :
                The database name or a BoundConnector instance
        '''
        if isinstance(target, BoundConnector):
            target = target.name
        super(self.__class__, self).__init__(target, overrideconnector)
        self._local = threading.local()
        log.d('init %s', self)

    def __repr__(self):
        return super(self.__class__, self).__repr__() + '[{0:x}]'.format(threading.current_thread().ident)

    def connection(self):
        '''Return a threadlocal connection object to talk to the bound database.'''
        try:
            conn = self._local.conn
        except AttributeError:
            conn = super(self.__class__, self).connection()
            self._local.conn = conn
        return conn


class _Transaction(object):

    _local = threading.local()

    def __init__(self, connector, comment=None):
        self.connector = connector
        self._stacks.setdefault(connector, [])
        self.comment = comment or ''

    def __repr__(self):
        return 'transaction {0!r}'.format(self.comment, self.connector)

    def __enter__(self):
        stack = self._stacks[self.connector]
        s = '{enter_self:40} @{connector}'.format(
            enter_self='    '*len(stack) + '---> ' + str(self),
            connector=self.connector
        )
        log.d(s)
        if not stack:
            conn = self.connector.connection()
            conn.isolation_level = 'IMMEDIATE'
        else:
            conn = stack[-1]
        stack.append(conn)
        return conn.cursor()

    def __exit__(self, exc_type, exception, traceback):
        stack = self._stacks[self.connector]
        conn = stack.pop()
        conn.isolation_level = None
        if not stack:
            del self._stacks[self.connector]
            if exc_type is None:
                conn.commit()
                log.d('COMMIT %s', self)
            else:
                conn.rollback()
                log.d('ROLLBACK %s', self)
        log.d('%s<--- %s', '    '*len(stack), self)

    @property
    def _stacks(self):
        try:
            return self._local.stacks
        except AttributeError:
            self._local.stacks = s = {}
            return s
