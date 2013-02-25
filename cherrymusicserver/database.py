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

import sqlite3
import threading

from contextlib import contextmanager
from operator import itemgetter

from cherrymusicserver import log


class SQLDatabase(object):

    def __init__(self, name):
        if not name:
            raise ValueError("illegal name %r: there must be a name" % name)
        self.__name = name
        self.__threadlocal = threading.local()
        self.Connection = type(
                               self.__class__.__name__ + '.Connection',
                               (sqlite3.Connection,),
                               {'close': self.__disconnect}
                               )

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__name)

    def __connect(self):
        try:
            return self.__threadlocal.conn
        except AttributeError:
            self.__threadlocal.conn = sqlite3.connect(self.__name, factory=self.Connection)
            log.d('thread %s connected to database %r', threading.current_thread(), self.__name)
            return self.__threadlocal.conn

    def __disconnect(self):
        try:
            conn = self.__threadlocal.conn
            del self.__threadlocal.conn
        except AttributeError:
            pass
        else:
            super(conn.__class__, conn).close()
            log.d('thread %s closed connection to database %r', threading.current_thread(), self.__name)

    def get_cursor(self):
        return self.__connect().cursor()

    @contextmanager
    def connection(self, mode=None):
        '''contextmanager; provides a connection that will auto-commit
        on clean exit and rollback on exception'''
        con = self.__connect()
        con.isolation_level = mode
        with con:
            yield con


class TableColumn(object):
    def __init__(self, name, datatype, attributes=''):
        self.name = name
        self.datatype = self.checkdatatype(datatype)
        self.attributes = attributes

    def sql(self):
        return ' '.join(["'" + self.name + "'", self.datatype, self.attributes])

    def checkdatatype(self, datatype):
        if datatype in ['int', 'text']:
            return datatype
        else:
            raise TypeError("column cannot have datatype: %s" % datatype)


class TableDescriptor(object):
    def __init__(self, tablename, columns):
        self.tablename = tablename
        self.columns = {}
        self.indexes = []
        for column in columns:
            if not type(column) == TableColumn:
                raise TypeError("column must be of type TableColumn")
            self.columns[column.name] = column

    def createOrAlterTable(self, sqlconn):
        updatedTable = False
        #table exists?
        if sqlconn.execute("""SELECT name FROM sqlite_master
            WHERE type='table' AND name=? """, (self.tablename,)).fetchall():
            dbtablelayout = sqlconn.execute("""PRAGMA table_info('%s')""" % self.tablename).fetchall()
            #map dict to column name
            dbtablelayout = dict((col[1], col) for col in dbtablelayout)
            #remove columns from db when not in template
            for columnname in dbtablelayout.keys():
                if columnname not in self.columns:
                    #can't do this in sqlite...
                    #log.i('Dropping column %s from table %s' % (columnname, self.tablename))
                    #sqlconn.execute("""ALTER TABLE %s DROP COLUMN %s"""%(self.tablename, columnname))
                    #updatedTable = True
                    pass
                else:
                    log.d('Column %s in table %s exists and needs no change' % (columnname, self.tablename))
            #add new columns to db when not in db
            for templatecolumnname, templatecolumn in self.columns.items():
                if templatecolumnname not in dbtablelayout.keys():
                    log.i('Adding column %s to table %s' % (templatecolumnname, self.tablename))
                    sqlconn.execute("""ALTER TABLE %s ADD COLUMN %s""" % (self.tablename, templatecolumn.sql()))
                    updatedTable = True
                else:
                    log.d('Column %s in table %s exists and needs no change' % (templatecolumnname, self.tablename))
            #TODO add checks for DEFAULT value and NOT NULL
        else:
            log.i('Creating table %s' % self.tablename)
            sqlconn.execute("""CREATE TABLE %s (%s)""" % (self.tablename, ', '.join(map(lambda x: x.sql(), self.columns.values()))))
            updatedTable = True
        return updatedTable

    def createIndex(self, sqlconn, columns):
        for c in columns:
            if not c in self.columns:
                raise IndexError('column %s does not exist in table %s, cannot create index!' % (c, self.tablename))
        existing_indexes = map(itemgetter(0), sqlconn.execute("""SELECT name FROM sqlite_master WHERE type='index' ORDER BY name""").fetchall())
        indexname = '_'.join(['idx', self.tablename, '_'.join(columns)])
        if not indexname in existing_indexes:
            log.i('Creating index %s' % indexname)
            sqlconn.execute('CREATE INDEX IF NOT EXISTS %s ON %s(%s)' % (indexname, self.tablename, ', '.join(columns)))

