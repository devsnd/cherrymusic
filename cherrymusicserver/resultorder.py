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

"""This class determines the order of the results
fetched from the database by some mystic-voodoo-
hocuspocus heuristics"""

from cherrymusicserver import util

class ResultOrder:
    def __init__(self, searchword):
        self.fullsearchterm = searchword.lower()
        self.searchwords = searchword.lower().split(' ')
        self.perfectMatchBias = 100
        self.partialPerfectMatchBias = 20
        self.startsWithMatchBias = 10
        self.folderBonus = 5
    def __call__(self,element):
        file = element.path
        isdir = element.dir
        fullpath = file.lower()
        file = util.filename(file).lower()
        bias = 0


        #count occurences of searchwords
        occurences=0
        for searchword in self.searchwords:
            if searchword in fullpath:
                occurences += 3 #magic number for bias
            else:
                occurences -= 10
            if searchword in file:
                occurences += 10 #magic number for bias"""
            else:
                occurences -= 10

        bias += occurences

        #perfect match?
        if file == self.fullsearchterm or self.noThe(file) == self.fullsearchterm:
            return bias+self.perfectMatchBias

        file = util.stripext(file)
        #partial perfect match?
        for searchword in self.searchwords:
            if file == searchword:
                if isdir:
                    bias += self.folderBonus
                return bias+self.partialPerfectMatchBias

        #file starts with match?
        for searchword in self.searchwords:
            if file.startswith(searchword):
                bias += self.startsWithMatchBias

        #remove possible track number
        while len(file)>0 and '0' <= file[0] and file[0] <= '9':
            file = file[1:]
        file = file.strip()
        for searchword in self.searchwords:
            if file == searchword:
                return bias + self.startsWithMatchBias

        return bias

    def noThe(self,a):
        if a.lower().endswith((', the',', die')):
            return a[:-5]
        return a
