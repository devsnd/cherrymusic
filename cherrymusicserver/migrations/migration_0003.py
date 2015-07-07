# -*- coding: utf-8 -*- #
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

""" Migrate album art filenames from old base64 encoding to md5 hash """

#python 2.6+ backward compability
from __future__ import unicode_literals

import base64
import codecs
import errno
import logging
import os
import re
import shutil
import sys

from cherrymusicserver import pathprovider

log = logging.getLogger(__name__)

_DONE_FILE = '.hashpath'
_MIGRATION_SUFFIX = '-migrated'

_ERR_MSG = """Error while migrating saved album art.

Fix the cause of the error and restart to continue.

Unmigrated files are in your album art folder:
    {{artfolder}}
Migrated files are in the migration folder:
    {{artfolder}}{suffix}

To abort the migration and lose the unmigrated album art:
    - delete or move the album art folder;
    - rename the migration folder by removing "{suffix}";
    - create a file "{donefile}" in the folder (file can be empty).
""".format(suffix=_MIGRATION_SUFFIX, donefile=_DONE_FILE)


def migrate():
    """ Migrate if necessary, exit(1) on error """
    artfolder = pathprovider.albumArtFilePath('')
    hashpathfile = os.path.join(artfolder, _DONE_FILE)
    if os.path.exists(hashpathfile):
        log.debug('Saved album art filenames already migrated. Skipping.')
        return

    try:
        log.info('Migrating saved album art filenames...')
        _migrate(artfolder)
    except:
        errmsg = _ERR_MSG.format(artfolder=artfolder)
        log.exception('Error during album art migration')
        log.critical(errmsg)
        sys.exit(1)
    else:
        open(hashpathfile, 'a').close()
        log.info('Album art filename migration done.')



def _migrate(sourcedir):
    """ migrate into different dir and then swap it in, to mitigate mishaps """
    targetdir = sourcedir.rstrip(os.path.sep) + _MIGRATION_SUFFIX
    try:
        os.mkdir(targetdir)
    except OSError as err:
        # ignore if targetdir exists to allow restarting aborted migrations
        if err.errno != errno.EEXIST:
            raise

    _base64_artfile_regex = re.compile(
        '^'
        '([\da-zA-Z+-]{4})*'             # pathprovider uses '-' instead of '\'
        '([\da-zA-Z+-]{3}=|[\da-zA-Z+-]{2}==)?'
        '$')
    is_base64 = lambda s: bool(_base64_artfile_regex.match(s))

    all_filenames = os.listdir(sourcedir)
    migratable_filenames = (f for f in all_filenames if is_base64(f))
    unmigratable_filenames = (f for f in all_filenames if not is_base64(f))

    # move any non-albumart files first (which shouldn't exist, but who knows)
    for filename in unmigratable_filenames:
        oldpath = os.path.join(sourcedir, filename)
        newpath = os.path.join(targetdir, filename)
        _move_if_exists(oldpath, newpath)

    # migrate albumart files
    for filename in migratable_filenames:
        ownerpath = _base64decode(filename)
        oldpath = os.path.join(sourcedir, filename)
        newname = os.path.basename(pathprovider.albumArtFilePath(ownerpath))
        newpath = os.path.join(targetdir, newname)
        _move_if_exists(oldpath, newpath)

    os.rmdir(sourcedir)
    os.rename(targetdir, sourcedir)

def _move_if_exists(oldpath, newpath):
    try:
        shutil.move(oldpath, newpath)
    except OSError as err:
        # ignore errors from existing newpath and missing oldpath,
        # which might occur if this migration is (concurrently) executed more
        # than once by mistake
        if err.errno not in (errno.EEXIST, errno.ENOENT):
            raise

def _base64decode(s):
    """ decode old albumart base64 encoding; copied code from pathprovider """
    utf8_bytestr = codecs.encode(s, 'UTF-8')
    utf8_altchar = codecs.encode('+-', 'UTF-8')
    return codecs.decode(base64.b64decode(utf8_bytestr, utf8_altchar), 'UTF-8')


if __name__ == "__main__":   # pragma: no cover
    migrate()
