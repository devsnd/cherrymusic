"""This class is the heart-piece of the program and
will delegate different calls between other classes.
"""

import os
from random import choice

from cherrymusic import util
from cherrymusic import resultorder

class CherryModel:
    def __init__(self,config, cache):
        self.config = config
        self.cache = cache

    def abspath(self,path):
        return os.path.join(self.config.config[self.config.BASEDIR],path)

    def strippath(self,path):
        if path.startswith(self.config.config[self.config.BASEDIR]):
            return path[len(self.config.config[self.config.BASEDIR])+1:]
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

        compactlisting = len(allfilesindir) > self.config.config[self.config.MAXSHOWFOLDERS]
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
                    musicentries.append(MusicEntry(self.strippath(subpath)))

                else:
                    musicentries.append(MusicEntry(self.strippath(subpath),dir=True))

        return musicentries

    def search(self, term):
        results = self.cache.searchfor(term,maxresults=self.config.config[self.config.MAXSEARCHRESULTS])
        results = sorted(results,key=resultorder.ResultOrder(term),reverse=True)
        results = results[:min(len(results),self.config.config[self.config.MAXSEARCHRESULTS])]
        ret = []
        for file in results:
            if os.path.isfile(os.path.join(self.config.config[self.config.BASEDIR],file)):
                ret.append(MusicEntry(self.strippath(file)))
            else:
                ret.append(MusicEntry(self.strippath(file),dir=True))
        return ret
   
    def saveplaylist(value):
        if not os.path.exists(dir):
            os.makedirs("playlists")
            
    def motd(self):
        artist = [ 'Hendrix',
                    'the Beatles',
                    'James Brown',
                    'Nina Simone',
                    'Mozart',
                    'Einstein',
                    'Bach']
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
                ]
        oneliner = choice(search)
        if '{artist}' in oneliner:
            oneliner=oneliner.replace('{artist}',choice(artist))
        return oneliner
        

class MusicEntry:
    def __init__(self, path, compact=False, dir=False, repr=None):
        self.path = path
        self.compact = compact
        self.dir = dir
        self.repr = repr