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
"""This class is the heart-piece of the program and
will delegate different calls between other classes.
"""

import os
from random import choice
import cherrypy

import cherrymusicserver as cherry
from cherrymusicserver import util
from cherrymusicserver import resultorder
from cherrymusicserver import log

class CherryModel:
    def __init__(self, cache):
        self.cache = cache

    def abspath(self,path):
        return os.path.join(cherry.config.media.basedir.str, path)

    def strippath(self,path):
        if path.startswith(cherry.config.media.basedir.str):
            return path[len(cherry.config.media.basedir.str) + 1:]
        return path

    def sortFiles(self,files,fullpath=''):
        #sort alphabetically (case insensitive)
        sortedfiles = sorted(files,
                            key=lambda x : util.filename(x).upper() )
        if not fullpath == '':
            #sort directories up
            sortedfiles = sorted(sortedfiles,
                                key=lambda x : os.path.isfile(os.path.join(fullpath,x)))
        return sortedfiles

    def listdir(self,dirpath,filterstr=''):
        absdirpath = self.abspath(dirpath)
        allfilesindir = os.listdir(absdirpath)

        #remove all files not inside the filter
        if not filterstr == '':
            filterstr = filterstr.upper()
            allfilesindir = list(filter(lambda x : x.upper().startswith(filterstr), allfilesindir))

        compactlisting = len(allfilesindir) > cherry.config.browser.maxshowfiles.int
        sortedfiles = self.sortFiles(allfilesindir, absdirpath)

        filterlength = len(filterstr)+1
        currentletter = '/' #impossible first character
        musicentries = []
        for dir in sortedfiles:
            subpath = os.path.join(absdirpath,dir)
            if compactlisting:
                if dir.upper().startswith(currentletter.upper()) and not len(currentletter)<filterlength:
                    continue
                else:
                    currentletter = dir[:filterlength]
                    musicentries.append(MusicEntry(self.strippath(absdirpath),repr=currentletter,compact=True))


            else:
                if os.path.isfile(subpath):
                    if self.isplayable(subpath):
                        musicentries.append(MusicEntry(self.strippath(subpath)))

                else:
                    musicentries.append(MusicEntry(self.strippath(subpath),dir=True))
        if musicentries == []:
            musicentries.append(MusicEntry(path="No playable media files found.", repr=""))
        return musicentries

    def search(self, term):
        user = cherrypy.session.get('username', None)
        if user:
            log.d(user+' searched for "'+term+'"')
        results = self.cache.searchfor(term, maxresults=cherry.config.search.maxresults.int)
        results = sorted(results,key=resultorder.ResultOrder(term),reverse=True)
        results = results[:min(len(results), cherry.config.search.maxresults.int)]
        ret = []
        for file in results:
            strippedpath = self.strippath(file)
            #let only playable files appear in the search results
            playable = self.isplayable(strippedpath)
            isfile = os.path.isfile(os.path.join(cherry.config.media.basedir.str, file))
            if isfile and not playable:
                continue

            if isfile:
                ret.append(MusicEntry(strippedpath))
            else:
                ret.append(MusicEntry(strippedpath,dir=True))

        return ret

    def isplayable(self, filename):
        '''checks to see if there's no extension or if the extension is in
        the configured 'playable' list'''
        ext = os.path.splitext(filename)[1]
        return not ext or ext[1:].lower() in cherry.config.media.playable.list

    def motd(self):
        artist = [  'Hendrix',
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
        search = [  'Wadda ya wanna hea-a?',
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
            oneliner=oneliner.replace('{artist}',a)
            if '{revartist}' in oneliner:
                oneliner=oneliner.replace('{revartist}',a.lower()[::-1])
        return oneliner

class MusicEntry:
    def __init__(self, path, compact=False, dir=False, repr=None):
        self.path = path
        self.compact = compact
        self.dir = dir
        self.repr = repr
