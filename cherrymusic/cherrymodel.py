"""This class is the heart-piece of the program and
will delegate different calls between other classes.
"""

import os
from random import choice
import cherrypy

import pickle #only used for playlists. delete when better soluiton available!

import cherrymusic as cherry
from cherrymusic import util
from cherrymusic import resultorder

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

        compactlisting = len(allfilesindir) > cherry.config.browser.maxshowfolders.int
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
        user = cherrypy.session.get('username', None)
        if user:
            print(user+' searched for "'+term+'"')
        results = self.cache.searchfor(term, maxresults=cherry.config.search.maxresults.int)
        results = sorted(results,key=resultorder.ResultOrder(term),reverse=True)
        results = results[:min(len(results), cherry.config.search.maxresults.int)]
        ret = []
        for file in results:
            strippedpath = self.strippath(file)
            #let only playable files appear in the search results
            playable = strippedpath.lower() in cherry.config.media.playable.list
            isfile = os.path.isfile(os.path.join(cherry.config.media.basedir.str, file))
            if isfile and not playable:
                continue
                
            if isfile:
                ret.append(MusicEntry(strippedpath))
            else:
                ret.append(MusicEntry(strippedpath,dir=True))

        return ret
              
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
        
    def savePlaylist(self, playlist, playlistname):
        if not os.path.exists('playlists'):
            os.makedirs("playlists")
        print(playlist)
        playlistname+='.pls'
        with open('playlists/'+playlistname,'wb') as f:
            pickle.dump(playlist,f)
        return 'success'
    
    def loadPlaylist(self, playlistname):
        with open('playlists/'+playlistname,'rb') as f:
            playlist = pickle.load(f)
            print(playlist)
            return playlist
        
    def showPlaylists(self):
        return os.listdir('playlists')
        

class MusicEntry:
    def __init__(self, path, compact=False, dir=False, repr=None):
        self.path = path
        self.compact = compact
        self.dir = dir
        self.repr = repr
