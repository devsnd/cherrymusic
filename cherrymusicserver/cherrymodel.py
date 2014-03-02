#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
"""This class is the heart-piece of the program and
will delegate different calls between other classes.
"""

from __future__ import unicode_literals

import os
from random import choice
import codecs
import json
import cherrypy
import audiotranscode
from imp import reload

try:
    from urllib.parse import quote
except ImportError:
    from backport.urllib.parse import quote
try:
    import urllib.request
except ImportError:
    import backport.urllib as urllib

import cherrymusicserver as cherry
from cherrymusicserver import service
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

    @classmethod
    def fileSortFunc(cls, filepath):
        upper = pathprovider.filename(filepath).upper()
        return upper

    @classmethod
    def fileSortFuncNum(cls, filepath):
        upper = CherryModel.fileSortFunc(filepath)
        if ' ' in upper:
            part_part = upper[:upper.index(' ')]
            # make sure that numbers are sorted correctly by evening out
            # the number in the filename 0-padding to 5 digits.
            if part_part.isdigit():
                return '0'*(5 - len(part_part)) + upper
        return upper

    def sortFiles(self, files, fullpath='', number_ordering=False):
        # sort alphabetically (case insensitive)
        if number_ordering:
            # make sure numbers are sorted correctly
            sortedfiles = sorted(files, key=CherryModel.fileSortFuncNum)
        else:
            sortedfiles = sorted(files, key=CherryModel.fileSortFunc)
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
        else:
            allfilesindir = [f for f in allfilesindir if not f.startswith('.')]

        musicentries = []

        maximum_shown_files = cherry.config['browser.maxshowfiles']
        compactlisting = len(allfilesindir) > maximum_shown_files
        if compactlisting:
            upper_case_files = [x.upper() for x in allfilesindir]
            filterstr = os.path.commonprefix(upper_case_files)
            filterlength = len(filterstr)+1
            currentletter = '/'  # impossible first character
            # don't care about natural number order in compact listing
            sortedfiles = self.sortFiles(allfilesindir, number_ordering=False)
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
            # enable natural number ordering for real directories and files
            sortedfiles = self.sortFiles(allfilesindir, absdirpath,
                                         number_ordering=True)
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
            log.d(_("%(user)s searched for '%(term)s'"), {'user': user, 'term': term})
        max_search_results = cherry.config['search.maxresults']
        results = self.cache.searchfor(term, maxresults=max_search_results)
        with Performance(_('sorting DB results using ResultOrder')) as perf:
            debug = tweaks.result_order_debug
            order_function = resultorder.ResultOrder(term, debug=debug)
            results = sorted(results, key=order_function, reverse=True)
            results = results[:min(len(results), max_search_results)]
            if debug:
                n = tweaks.result_order_debug_files
                for sortedResults in results[:n]:
                    perf.log(sortedResults.debugOutputSort)
                for sortedResults in results:
                    sortedResults.debugOutputSort = None  # free ram

        with Performance(_('checking and classifying results:')):
            results = list(filter(isValidMediaFile, results))
        return results

    def check_for_updates(self):
        try:
            url = 'http://fomori.org/cherrymusic/update_check.php?version='
            url += cherry.__version__
            urlhandler = urllib.request.urlopen(url, timeout=5)
            jsondata = codecs.decode(urlhandler.read(), 'UTF-8')
            versioninfo = json.loads(jsondata)
            return versioninfo
        except Exception as e:
            log.e(_('Error fetching version info: %s') % str(e))
            return []
    def motd(self):
        artist = ['Hendrix',
                  'Miles Davis',
                  'James Brown',
                  'Nina Simone',
                  'Mozart',
                  'Bach',
                  'John Coltraine',
                  'Jim Morrison',
                  'Frank Sinatra',
                  'Django Reinhardt',
                  'Kurt Cobain',
                  'Thom Yorke',
                  'Vivaldi',
                  'Bob Dylan',
                  'Johnny Cash',
                  'James Brown',
                  'Bob Marley',
                  'Björk']
        liquid = ['2 liters of olive oil',
                  'a glass of crocodile tears',
                  'a bowl of liquid cheese',
                  'some battery acid',
                  'cup of grog',
                  ]
        search = ['{artist} can turn diamonds into jelly-beans.',
                  'The french have some really stinky cheese. It\'s true.',
                  '{artist} used to eat squids for breakfast.',
                  'The GEMA wont let me hear {artist}.',
                  'If {artist} had played with {artist}, they would have made bazillions!',
                  '{artist} actually stole everything from {artist}.',
                  '{artist} really liked to listen to {artist}.',
                  '{artist}\'s music played backwards is actually the same as {artist}. This is how they increased their profit margin!',
                  '{artist} always turned the volume up to 11.',
                  'If {artist} made Reggae it sounded like {artist}.',
                  '{artist} backwards is "{revartist}".',
                  '2 songs of {artist} are only composed of haikus.',
                  '{artist} drank {liquid} each morning, sometimes even twice a day.',
                  'Instead of soap, {artist} used {liquid} to shower.',
                  '{artist} had a dog the size of {artist}.',
                  '{artist} was once sued by {artist} for eating all the cake.',
                  '{artist} named his cat after {artist}. It died two years later by drowning in {liquid}.',
                  '{artist} once founded a gang, but then had to quit becaus of the pirates. All former gang members became squirrels.',
                  '{artist}, a.k.a. "Quadnostril" actually had 2 noses. This meant that it was quite hard to be taken seriously.',
                  'Never put {liquid} and {artist} in the same room. Never ever!',
                  '{artist} lived twice, once as a human, once as a duck.',
                  'Nobody ever thought {artist} would still be famous after the great goat-cheese-fiasco.',
                  'For a long time, nobody knew that {artist} secretly loved wall sockets.',
                  'In the beginning {artist} was very poor and had to auction off a pinky toe. It is still exhibited in the "museum of disgusting stuff" in paris.',
                  '{artist} did never mind if somebody made weird noises. Occasionally this was the inspiration for a new song.',
                  'While creating a huge camp fire {artist} lost all hair. It took years for it to regrow.',
                  'A rooster isn\'t necessarily better than a balloon. However, {artist} found out that balloons are less heavy.',
                  'Instead of cars, snow mobiles are often used to move around in the alps. This information has no relevance whatsoever.',
                  'Creating new life-forms always was a hobby of {artist}. The greatest success was the creation of {artist}.',
                  ]
        oneliner = choice(search)
        while '{artist}' in oneliner:
            a = choice(artist)
            oneliner = oneliner.replace('{artist}', a, 1)
            if '{revartist}' in oneliner:
                oneliner = oneliner.replace('{revartist}', a.lower()[::-1])
        if '{liquid}' in oneliner:
            oneliner = oneliner.replace('{liquid}', choice(liquid))
        return oneliner

    def randomMusicEntries(self, count):
        loadCount = int(count * 1.5) + 1           # expect 70% valid entries
        entries = self.cache.randomFileEntries(loadCount)
        filteredEntries = list(filter(isValidMediaFile, entries))

        return filteredEntries[:count]


def isValidMediaFile(file):
    file.path = strippath(file.path)
    #let only playable files appear in the search results
    if file.path.startswith('.'):
        return False
    if not isplayable(file.path) and not file.dir:
        return False
    return True


def isplayable(filename):
    '''checks to see if there's no extension or if the extension is in
    the configured 'playable' list'''
    ext = os.path.splitext(filename)[1]
    return ext and ext[1:].lower() in CherryModel.supportedFormats


def strippath(path):
    if path.startswith(cherry.config['media.basedir']):
        return os.path.relpath(path, cherry.config['media.basedir'])
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
            return {'type': 'dir',
                    'path': self.path,
                    'label': simplename}
        else:
            #file
            simplename = pathprovider.filename(self.path)
            urlpath = quote(self.path.encode('utf8'))
            return {'type': 'file',
                    'urlpath': urlpath,
                    'path': self.path,
                    'label': simplename}

    def __repr__(self):
        return "<MusicEntry path:%s, dir:%s>" % (self.path, self.dir)
