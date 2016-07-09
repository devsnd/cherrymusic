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

"""This class determines the order of the results
fetched from the database by some mystic-voodoo-
hocuspocus heuristics"""

from cherrymusicserver import pathprovider
from cherrymusicserver import log
import cherrymusicserver.tweak
from imp import reload
from cherrymusicserver.util import Performance

class ResultOrder:
    def __init__(self, searchword, debug=False):
        self.debug = debug
        self.fullsearchterm = searchword.lower()
        self.searchwords = searchword.lower().split(' ')

        reload(cherrymusicserver.tweak)
        self.perfect_match_bonus = cherrymusicserver.tweak.ResultOrderTweaks.perfect_match_bonus
        self.partial_perfect_match_bonus = cherrymusicserver.tweak.ResultOrderTweaks.partial_perfect_match_bonus
        self.starts_with_bonus = cherrymusicserver.tweak.ResultOrderTweaks.starts_with_bonus
        self.folder_bonus = cherrymusicserver.tweak.ResultOrderTweaks.folder_bonus
        self.word_in_file_name_bonus = cherrymusicserver.tweak.ResultOrderTweaks.word_in_file_name_bonus
        self.word_not_in_file_name_penalty = cherrymusicserver.tweak.ResultOrderTweaks.word_not_in_file_name_penalty
        self.word_in_file_path_bonus = cherrymusicserver.tweak.ResultOrderTweaks.word_in_file_path_bonus
        self.word_not_in_file_path_penalty = cherrymusicserver.tweak.ResultOrderTweaks.word_not_in_file_path_penalty
    def __call__(self,element):
        file = element.path
        isdir = element.dir
        fullpath = file.lower()
        filename = pathprovider.filename(file).lower()
        filename_words = filename.split(' ')

        bias = 0
        occurences_bias = 0
        perfect_match_bias = 0
        partial_perfect_match_bias = 0
        folder_bias = 0
        starts_with_bias = 0
        starts_with_no_track_number_bias = 0

        #count occurences of searchwords
        occurences=0
        for searchword in self.searchwords:
            if searchword in fullpath:
                occurences_bias += self.word_in_file_path_bonus
            else:
                occurences_bias += self.word_not_in_file_path_penalty
            if searchword in filename:
                occurences_bias += self.word_in_file_name_bonus
            else:
                occurences_bias += self.word_not_in_file_name_penalty

        #perfect match?
        if filename == self.fullsearchterm or self.noThe(filename) == self.fullsearchterm:
            perfect_match_bias += self.perfect_match_bonus

        filename = pathprovider.stripext(filename)
        #partial perfect match?
        for searchword in self.searchwords:
            if searchword in filename_words:
                partial_perfect_match_bias += self.partial_perfect_match_bonus
        if isdir:
            folder_bias += self.folder_bonus

        #file starts with match?
        for searchword in self.searchwords:
            if filename.startswith(searchword):
                starts_with_bias += self.starts_with_bonus

        #remove possible track number
        while len(filename)>0 and '0' <= filename[0] <= '9':
            filename = filename[1:]
        filename = filename.strip()
        for searchword in self.searchwords:
            if filename == searchword:
                starts_with_no_track_number_bias += self.starts_with_bonus

        bias = occurences_bias + perfect_match_bias + partial_perfect_match_bias + folder_bias + starts_with_bias + starts_with_no_track_number_bias

        if self.debug:
            element.debugOutputSort = '''
fullsearchterm: %s
searchwords: %s
filename: %s
filepath: %s
occurences_bias                  %d
perfect_match_bias               %d
partial_perfect_match_bias       %d
folder_bias                      %d
starts_with_bias                 %d
starts_with_no_track_number_bias %d
------------------------------------
total bias                       %d
            ''' % (
        self.fullsearchterm,
        self.searchwords,
        filename,
        fullpath,
        occurences_bias,
        perfect_match_bias,
        partial_perfect_match_bias,
        folder_bias,
        starts_with_bias,
        starts_with_no_track_number_bias,
        bias)

        return bias

    def noThe(self,a):
        if a.lower().endswith((', the',', die')):
            return a[:-5]
        return a
