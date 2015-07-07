#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2015 Tom Wallroth & Tilman Boerner
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
""" Contains migrations of CherryMusic data; for database migrations, see
    the database package.

    A migration is a module named `migration_nnnn` , where `nnnn` is one of a
    series of consecutive integers starting with `0001`.

    A migration has a `migrate()` function which will be called to execute the
    migration; the function is expected to decide whether the migration should
    be carried out or not. If a migration requires manual intervention or needs
    to be aborted for any reason, the function should print an actionable error
    message and sys.exit with an error status.
"""

#python 2.6+ backward compability
from __future__ import unicode_literals

import os
import pkgutil
import re

from backport import callable   # Py 3.0 and 3.1 compat


_MIGRATIONS_PATH = os.path.dirname(__file__)
_NAME_PATTERN = re.compile('^migration_\d{4}$')


def check_and_migrate_all():
    """ Runs all necessary migrations in alphabetical order.

        The program can sys.exit if manual intervention is required.
    """
    for migration in iter_load_migrations():
        migration.migrate()


def iter_load_migrations():
    """ Generator which imports and returns all migration modules in
        alphabetical order.
    """
    itermods = pkgutil.iter_modules([_MIGRATIONS_PATH])
    modnames = sorted(name for _, name, ispkg in itermods
        if not ispkg and _NAME_PATTERN.match(name))
    return (_import_migration(name) for name in modnames)


def _import_migration(modulename):
    qualname = 'cherrymusicserver.migrations.' + modulename
    mig = __import__(qualname, fromlist='dummy')
    if not callable(getattr(mig, 'migrate', None)):
        raise TypeError('Migration needs a `migrate` function: ' + mig.__name__)
    return mig
