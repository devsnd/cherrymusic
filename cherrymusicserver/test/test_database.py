#!/usr/bin/env python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
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

import unittest
import sqlite3
import os


from cherrymusicserver import log
log.setTest()

import cherrymusicserver.database.defs as defs
from cherrymusicserver.database.sql import MemConnector


class TestDefs(unittest.TestCase):

    def setUp(self):
        defdir = os.path.dirname(defs.__file__)
        dbnames = tuple(n for n in os.listdir(defdir) if not n.startswith('__'))
        self.defs = dict((name, defs.get(name)) for name in dbnames)

    def test_all_databases_are_defined(self):
        required = ('cherry.cache', 'playlist', 'user', 'useroptions')
        missing = set(required) - set(self.defs)
        assert not missing, "no database definitions must be missing " + str(missing)

    def test_versionnames_are_all_ints(self):
        def check(dbdef):
            "version names must all be integers"
            nonint = [version for version in dbdef if not version.isdigit()]
            if nonint:
                yield nonint
        self.run_forall_defs(check)

    def test_versionnames_are_consecutive_starting_0_or_1(self):
        def check(dbdef):
            "versions must be consecutive and start with 0 or 1"
            versions = sorted(int(v) for v in dbdef)
            min, max = versions[0], versions[-1]
            expected = list(range(1 if min else 0, max + 1))
            if expected != versions:
                yield versions
        self.run_forall_defs(check)

    def test_versionkeys_required_are_present(self):
        required = ('create.sql', 'drop.sql', 'update.sql')
        initially_ok = ('update.sql',)

        def check(dbdef):
            "database version must include required keys"
            for vnum, vdef in dbdef.items():
                missing = set(required) - set(vdef)
                if vnum == min(dbdef):
                    missing -= set(initially_ok)
                if missing:
                    yield vnum, missing
        self.run_forall_defs(check)

    def test_versionpermutations_are_updatable(self):
        def check(dbdef):
            "incremental updates must work for all versions"
            start, stop = int(min(dbdef)), int(max(dbdef)) + 1
            program = ((i, range(i + 1, stop)) for i in range(start, stop))
            for base, updates in program:
                connector = MemConnector().bound(None)  # new MemConnector for fresh db
                try:
                    create(dbdef, base, connector)
                    update(dbdef, updates, connector)
                except AssertionError as e:
                    yield 'base version: {0} {1}'.format(base, e.args[0])
                    break   # don't accumulate errors
        self.run_forall_defs(check)

    def test_versionremoval_drop_clears_db(self):
        def check(dbdef):
            "drop script must clear the database"
            for version in dbdef:
                connector = MemConnector().bound(None)
                create(dbdef, version, connector)
                drop(dbdef, version, connector)
                remaining = connector.execute(
                    "SELECT * FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                ).fetchall()
                if remaining:
                    yield '{0}:drop.sql'.format(version), remaining
        self.run_forall_defs(check)

    def run_forall_defs(self, check):
        errors = []
        for dbname, dbdef in self.defs.items():
            for error in check(dbdef):
                errors += ['{0}: {1}: {2}'.format(check.__doc__, dbname, error)]
        assert not errors, os.linesep + os.linesep.join(errors)


def create(dbdef, vnum, connector):
    with connector.connection() as c:
        runscript(dbdef, vnum, 'create.sql', c)
        runscript(dbdef, vnum, 'after.sql', c, missing_ok=True)


def drop(dbdef, vnum, connector):
    with connector.connection() as c:
        runscript(dbdef, vnum, 'drop.sql', c)


def update(dbdef, vnums, connector):
    for vnum in vnums:
        with connector.connection() as c:
            runscript(dbdef, vnum, 'update.sql', c)
            runscript(dbdef, vnum, 'after.sql', c, missing_ok=True)


def runscript(dbdef, vnum, scriptname, conn, missing_ok=False):
    '''Run an SQL script, statement per statement, and give a helpful
    message on error.
    '''
    try:
        script = dbdef[str(vnum)][scriptname]
    except KeyError:
        if missing_ok:
            return
        raise
    lno = 1
    for stmt in split_sqlscript(script):
        linecount = stmt.count('\n')   # yeah, linux linesep.
        try:
            cursor = conn.cursor()
            cursor.execute(stmt.strip())
        except sqlite3.Error as e:
            if stmt.splitlines() and not stmt.splitlines()[0].strip():  # skip 1st line if empty
                lno += 1
                linecount -= 1
            msg = '{br}{script}:{br}{listing}{br}{br}{error}'.format(
                script='{0}:{1}:{2}'.format(vnum, scriptname, lno),
                listing=os.linesep.join(script_lines(script, lno, linecount + 1)),
                error=e,
                br=os.linesep)
            raise AssertionError(msg)
        else:
            lno += linecount
        finally:
            cursor.close()


def split_sqlscript(script):
    import re
    stmts = [x + ';' for x in script.split(';')]
    i = 0
    while i < len(stmts):
        if re.search(r'\bBEGIN\b', stmts[i], re.I):
            while (i + 1) < len(stmts) and not re.search(r'\bEND\b', stmts[i], re.I):
                stmts[i] += stmts[i + 1]
                del stmts[i + 1]
                if re.search(r'\bEND\b', stmts[i], re.I):
                    break
        i += 1
    return stmts


def script_lines(script, start=1, length=0):
    '''A range of lines from a text file, including line number prefix.'''
    stop = start + length
    gutterwidth = len(str(stop)) + 1
    i = 0
    for line in script.splitlines()[start - 1:stop - 1]:
        yield '{n:{w}}| {line}'.format(
            n=start + i,
            w=gutterwidth,
            line=line
        )
        i += 1


if __name__ == '__main__':
    unittest.main()
