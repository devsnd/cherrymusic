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

"""This file contains all static values that can be used to tweak the
program execution. All classes are static and only contain simple values.
To use this class, please import it using the fully classified module name, e.g

    import cherrymusicserver.tweak

To account for changes while the server is running, reload the module
before using it:

    reload(cherrymusicserver.tweak)

make sure to have reload imported as well:

    from imp import reload
"""

class ResultOrderTweaks:
    perfect_match_bonus = 100
    partial_perfect_match_bonus = 30
    starts_with_bonus = 10
    folder_bonus = 5
    word_in_file_name_bonus = 20
    word_not_in_file_name_penalty = -30
    word_in_file_path_bonus = 3
    word_not_in_file_path_penalty = -10

class CherryModelTweaks:
    result_order_debug = False
    result_order_debug_files = 10

class SearchTweaks:
    normal_file_search_limit = 400

