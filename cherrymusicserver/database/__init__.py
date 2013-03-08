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
"""CherryMusic database definition, versioning and control.

To support schema changes that are not backward-compatible, databases can be
versioned.
"""

from cherrymusicserver import log
from cherrymusicserver.database import defs
from cherrymusicserver.database import sql


def require(dbname, version):
    """Make sure the database exists and has the given version."""
    if not dbname:
        raise ValueError('dbname must not be empty or None')
    isversion = MultiUpdater.checkversion(dbname)
    assert isversion == version, '{0!r}: bad version: {1!r} (want: {2!r})'.format(dbname, isversion, version)


def ensure_requirements(dbname=None, autoconsent=False, consent_callback=None):
    '''Make sure all defined databases exist and are up to date.

    Will connect to all these databases and try to update them, if
    necessary, possibly asking the user for consent.

    dbname : str
        When given, only make sure of the database with that name.
    autoconsent : bool
        When ``True``, don't ask for consent, ever.
    consent_callback: callable
        Called when an update requires user consent; if the return value
        does not evaluate to ``True``, abort don't run any updates and
        return ``False``. If no callback is given or autoconsent == True,
        the value of autoconsent will be used to decide if the update
        should run.
    Returns : bool
        ``True`` if requirements are met.
    '''
    if autoconsent or consent_callback is None:
        consent_callback = lambda: autoconsent
    assert callable(consent_callback), (type(consent_callback))
    update = _create_updater(dbname)
    if update.needed:
        log.i('database definition out of date')
        if update.requires_consent and not consent_callback():
            return False
        update.run()
        log.i('database definition updated')
    return True


def resetdb(dbname):
    '''Delete all content and defined data structures from a database.

    Raises:
        ValueError : If dbname is ``None`` or empty, or not a defined database name.
    '''
    if not dbname:
        raise ValueError('dbname must not be empty or None')
    updater = _create_updater(dbname)
    updater.reset()


def _create_updater(*dbnames):
    return MultiUpdater(tuple(n for n in dbnames if n is not None))


class MultiUpdater(object):
    '''Manage the state of multiple databases at once.

    defs : dict
        Definitions of all databases to manage.
    connector : :class:`.connect.AbstractConnector`
        For connecting to the databases.
    '''
    def __init__(self, dbnames=()):
        dbdefs = defs.getall() if not dbnames else dict((n, defs.get(n)) for n in dbnames)
        self.updaters = tuple(sql.Updater(k, dbdefs[k]) for k in dbdefs)

    def __iter__(self):
        return iter(self.updaters)

    @property
    def needed(self):
        """``True`` if any database needs updating.

        See :meth:`.sql.Updater.needed`.
        """
        for u in self:
            if u.needed:
                return True
        return False

    @property
    def requires_consent(self):
        """``True`` if any database update needs user consent.

        See :meth:`.sql.Updater.requires_consent`.
        """
        for u in self:
            if u.requires_consent:
                return True
        return False

    def run(self):
        """Update all databases with out of date versions.

        See :meth:`.sql.Updater.run`.
        """
        for u in self:
            if u.needed:
                u.run()

    def reset(self):
        """Delete content and data structures of all included databases.

        See :meth:`.sql.Updater.reset`.
        """
        for u in self:
            u.reset()

    @classmethod
    def checkversion(self, dbname):
        """Return the effective version of a database."""
        return sql.Updater(dbname, defs.get(dbname))._version
