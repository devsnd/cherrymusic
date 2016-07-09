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
"""CherryMusic database definition, versioning and control.

To support schema changes that are not backward-compatible, databases can be
versioned.
"""

import itertools

from cherrymusicserver import log
from cherrymusicserver.database import defs
from cherrymusicserver.database import sql


def require(dbname, version):
    """ Raise an AssertionError if the database does not exist or has the wrong
        version.
    """
    if not dbname:
        raise ValueError('dbname must not be empty or None')
    isversion = MultiUpdater.checkversion(dbname)
    assert isversion == version, (
        '{0!r}: bad version: {1!r} (want: {2!r})'.format(
            dbname, isversion, version))


def ensure_current_version(dbname=None, autoconsent=False, consentcallback=None):
    '''Make sure all defined databases exist and are up to date.

    Will connect to all these databases and try to update their layout, if
    necessary, possibly asking the user for consent.

    dbname : str
        When given, only make sure of the database with that name.
    autoconsent : bool
        When ``True``, don't ask for consent, ever.
    consentcallback: callable
        Called when an update requires user consent; if the return value
        does not evaluate to ``True``, abort don't run any updates and
        return ``False``. If no callback is given or autoconsent == True,
        the value of autoconsent will be used to decide if the update
        should run.
    Returns : bool
        ``True`` if requirements are met.
    '''
    if autoconsent or consentcallback is None:
        consentcallback = lambda _: autoconsent
    with MultiUpdater(dbname) as update:
        if update.needed:
            if update.requires_consent and not consentcallback(update.prompts):
                return False
            log.w("Database schema update; don't turn off the program!")
            update.run()
            log.i('Database schema update complete.')
    return True


def resetdb(dbname):
    '''Delete all content and defined data structures from a database.

    Raises:
        ValueError : If dbname is ``None`` or empty, or not a defined database
        name.
    '''
    if not dbname:
        raise ValueError('dbname must not be empty or None')
    with MultiUpdater(dbname) as updater:
        updater.reset()


class MultiUpdater(object):
    '''Manage the state of multiple databases at once.

    defs : dict
        Definitions of all databases to manage.
    connector : :class:`.connect.AbstractConnector`
        For connecting to the databases.
    '''
    def __init__(self, dbname=None):
        if dbname is None:
            dbdefs = defs.getall()
            self.updaters = tuple(sql.Updater(k, dbdefs[k]) for k in dbdefs)
        else:
            self.updaters = (sql.Updater(dbname, defs.get(dbname)),)

    def __iter__(self):
        return iter(self.updaters)

    def __enter__(self):
        for updater in self:
            updater._lock()
        return self

    def __exit__(self, exctype, exception, traceback):
        for updater in self:
            updater._unlock()

    @property
    def needed(self):
        """``True`` if any database needs updating.

        See :meth:`.sql.Updater.needed`.
        """
        for updater in self:
            if updater.needed:
                return True
        return False

    @property
    def requires_consent(self):
        """``True`` if any database update needs user consent.

        See :meth:`.sql.Updater.requires_consent`.
        """
        for updater in self:
            if updater.requires_consent:
                return True
        return False

    @property
    def prompts(self):
        """An iterable of string prompts for updates that require consent."""
        return itertools.chain(*(updater.prompts for updater in self))

    def run(self):
        """Update all databases with out of date versions.

        See :meth:`.sql.Updater.run`.
        """
        for updater in self:
            if updater.needed:
                updater.run()

    def reset(self):
        """Delete content and data structures of all included databases.

        See :meth:`.sql.Updater.reset`.
        """
        for updater in self:
            updater.reset()

    @classmethod
    def checkversion(self, dbname):
        """Return the effective version of a database."""
        with sql.Updater(dbname, defs.get(dbname)) as updater:
            return updater._version
