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
"""Prompts for manual migration of CherryMusic config and data to XDG dirs

See https://github.com/devsnd/cherrymusic/issues/224
"""

#python 2.6+ backward compability
from __future__ import unicode_literals

import os
import sys

from cherrymusicserver import pathprovider

def migrate():
    """If config file is still in old location, print a message and exit(1)"""
    if pathprovider.configurationFileExists() or not pathprovider.fallbackPathInUse():
        return
    _printMigrationNotice()
    sys.exit(1)


def _printMigrationNotice():
    print(_("""
==========================================================================
Oops!

CherryMusic changed some file locations while you weren't looking.
(To better comply with best practices, if you wanna know.)

To continue, please move the following:

$ mv {src} {tgt}""".format(
        src=os.path.join(pathprovider.fallbackPath(), 'config'),
        tgt=pathprovider.configurationFile()) + """

$ mv {src} {tgt}""".format(
        src=os.path.join(pathprovider.fallbackPath(), '*'),
        tgt=pathprovider.getUserDataPath()) + """

Thank you, and enjoy responsibly. :)
==========================================================================
"""))
