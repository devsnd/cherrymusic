#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
"""This class is the heart-piece of the program and
will delegate different calls between other classes.
"""

from __future__ import unicode_literals

import os
import sys
from random import choice
import cherrypy
import audiotranscode
from imp import reload

try:
    from urllib.parse import quote
except ImportError:
    from backport.urllib.parse import quote

import cherrymusicserver as cherry
from cherrymusicserver import service
from cherrymusicserver import util
from cherrymusicserver import pathprovider
from cherrymusicserver.util import Performance
from cherrymusicserver import resultorder
from cherrymusicserver import log


@service.user(cache='filecache')
class CherryModel:
    def __init__(self):
        CherryModel.NATIVE_BROWSER_FORMATS = ['ogg', 'mp3']
        CherryModel.supportedFormats = CherryModel.NATIVE_BROWSER_FORMATS[:]
        if cherry.config['media.transcode']:
            self.transcoder = audiotranscode.AudioTranscode()
            CherryModel.supportedFormats += self.transcoder.availableDecoderFormats()
            CherryModel.supportedFormats = list(set(CherryModel.supportedFormats))

    def abspath(self, path):
        return os.path.join(cherry.config['media.basedir'], path)

    def sortFiles(self, files, fullpath=''):
        upper_case_filename = lambda x: pathprovider.filename(x).upper()
        #sort alphabetically (case insensitive)
        sortedfiles = sorted(files, key=upper_case_filename)
        if fullpath:
            #sort directories up
            isfile = lambda x: os.path.isfile(os.path.join(fullpath, x))
            sortedfiles = sorted(sortedfiles, key=isfile)
        return sortedfiles

    def listdir(self, dirpath, filterstr=''):
        absdirpath = self.abspath(dirpath)
        if cherry.config['browser.pure_database_lookup']:
            allfilesindir = self.cache.listdir(dirpath)
        else:
            allfilesindir = os.listdir(absdirpath)

        #remove all files not inside the filter
        if filterstr:
            filterstr = filterstr.lower()
            allfilesindir = [f for f in allfilesindir
                             if f.lower().startswith(filterstr)]

        musicentries = []

        maximum_shown_files = cherry.config['browser.maxshowfiles']
        compactlisting = len(allfilesindir) > maximum_shown_files
        if compactlisting:
            upper_case_files = [x.upper() for x in allfilesindir]
            filterstr = os.path.commonprefix(upper_case_files)
            filterlength = len(filterstr)+1
            currentletter = '/'  # impossible first character
            sortedfiles = self.sortFiles(allfilesindir)
            for dir in sortedfiles:
                filter_match = dir.upper().startswith(currentletter.upper())
                if filter_match and not len(currentletter) < filterlength:
                    continue
                else:
                    currentletter = dir[:filterlength]
                    #if the filter equals the foldername
                    if len(currentletter) == len(filterstr):
                        subpath = os.path.join(absdirpath, dir)
                        self.addMusicEntry(subpath, musicentries)
                    else:
                        musicentries.append(
                            MusicEntry(strippath(absdirpath),
                                       repr=currentletter,
                                       compact=True))
        else:
            sortedfiles = self.sortFiles(allfilesindir, absdirpath)
            for dir in sortedfiles:
                subpath = os.path.join(absdirpath, dir)
                self.addMusicEntry(subpath, musicentries)
        return musicentries

    def addMusicEntry(self, fullpath, list):
        if os.path.isfile(fullpath):
            if isplayable(fullpath):
                list.append(MusicEntry(strippath(fullpath)))
        else:
            list.append(MusicEntry(strippath(fullpath), dir=True))

    def updateLibrary(self):
        self.cache.full_update()
        return True

    def file_size_within_limit(self, filelist, maximum_download_size):
        acc_size = 0
        for f in filelist:
            acc_size += os.path.getsize(self.abspath(f))
            if acc_size > maximum_download_size:
                return False
        return True

    def search(self, term):
        reload(cherry.tweak)
        tweaks = cherry.tweak.CherryModelTweaks
        user = cherrypy.session.get('username', None)
        if user:
            log.d(user+' searched for "'+term+'"')
        max_search_results = cherry.config['search.maxresults']
        results = self.cache.searchfor(term, maxresults=max_search_results)
        with Performance('sorting DB results using ResultOrder'):
            debug = tweaks.result_order_debug
            order_function = resultorder.ResultOrder(term, debug=debug)
            results = sorted(results, key=order_function, reverse=True)
            results = results[:min(len(results), max_search_results)]
            if debug:
                n = tweaks.result_order_debug_files
                for sortedResults in results[:n]:
                    Performance.log(sortedResults.debugOutputSort)
                for sortedResults in results:
                    sortedResults.debugOutputSort = None  # free ram

        with Performance('checking and classifying results:'):
            results = list(filter(isValidMediaFile, results))
        return results

    def motd(self):
        artist = ['Hendrix',
                  'the Beatles',
                  'James Brown',
                  'Nina Simone',
                  'Mozart',
                  'Einstein',
                  'Bach',
                  'John Coltraine',
                  'Deep Purple',
                  'Frank Sinatra',
                  'Django Reinhardt',
                  'Radiohead',
                  'The chemical brothers',
                  'Vivaldi',
                  'Björk']
        search = ['Wadda ya wanna hea-a?',
                  'I would like to dance to',
                  'Someone told me to listen to',
                  'There is nothing better than',
                  'The GEMA didnt let me hear',
                  'Give me',
                  'If only {artist} had played with',
                  'My feet cant stop when I hear',
                  '{artist} actually stole everything from',
                  '{artist} really liked to listen to',
                  '{artist} played backwards is actually',
                  'Each Beatle had sex with',
                  'Turn the volume up to 11, it\'s',
                  'If {artist} made Reggae it sounded like',
                  '{artist} backwards is "{revartist}"',
                  '2 songs of {artist} are only composed of haikus.',
                  '{artist} used to sing with',
                  '{artist} had a dog the size of',
                  '{artist} was once sued by',
                  '{artist} named his dog after',
                  '{artist} claimed to be funkier than',
                  '{artist} could never stand the music of',
                  '{artist} could not stop listening to',
                  '{artist} was once interviewed by',
                  '{artist} actually has 2 noses.',
                  ]
        oneliner = choice(search)
        if '{artist}' in oneliner:
            a = choice(artist)
            oneliner = oneliner.replace('{artist}', a)
            if '{revartist}' in oneliner:
                oneliner = oneliner.replace('{revartist}', a.lower()[::-1])
        return oneliner

    def randomMusicEntries(self, count):
        loadCount = int(count * 1.5) + 1           # expect 70% valid entries
        entries = self.cache.randomFileEntries(loadCount)
        filteredEntries = list(filter(isValidMediaFile, entries))

        return filteredEntries[:count]

def isValidMediaFile(file):
    file.path = strippath(file.path)
    #let only playable files appear in the search results
    if not isplayable(file.path) and not file.dir:
        return False
    return True


def createMusicEntryByFilePath(file):
    """DEPRECATED, files are checked using isValidMediaFile(MusicEntry) now"""
    strippedpath = strippath(file)
    #let only playable files appear in the search results
    playable = isplayable(strippedpath)
    fullpath = os.path.join(cherry.config['media.basedir'], file)

    if not os.path.exists(fullpath):
        log.w('search found inexistent file: %r', file)
        return []

    isfile = os.path.isfile(fullpath)
    if isfile and not playable:
        return []

    if isfile:
        return [MusicEntry(strippedpath)]
    else:
        return [MusicEntry(strippedpath, dir=True)]


def isplayable(filename):
    '''checks to see if there's no extension or if the extension is in
    the configured 'playable' list'''
    ext = os.path.splitext(filename)[1]
    return ext and ext[1:].lower() in CherryModel.supportedFormats


def strippath(path):
    if path.startswith(cherry.config['media.basedir']):
        return path[len(cherry.config['media.basedir']) + 1:]
    return path

class MusicEntry:
    def __init__(self, path, compact=False, dir=False, repr=None):
        self.path = path
        self.compact = compact
        self.dir = dir
        self.repr = repr

    def to_dict(self):
        if self.compact:
            #compact
            return {'type': 'compact',
                    'urlpath': self.path,
                    'label': self.repr}
        elif self.dir:
            #dir
            simplename = pathprovider.filename(self.path)
            return {'type':'dir',
                    'path':self.path,
                    'label':simplename }
        else:
            #file
            simplename = pathprovider.filename(self.path)
            urlpath = quote(self.path.encode('utf8'));
            return {'type':'file',
                    'urlpath':urlpath,
                    'path':self.path,
                    'label':simplename}

    def __repr__(self):
        return "<MusicEntry path:%s, dir:%s>" % (self.path, self.dir)
