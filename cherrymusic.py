import cherrypy
import os
from random import choice
import pickle
from time import time
from urllib.parse import quote
import hashlib

class CherryModel:
    def __init__(self,config, cache):
        self.config = config
        self.cache = cache

    def filename(path,pathtofile=False):
        if pathtofile:
            return os.path.split(path)[0]
        else:
            return os.path.split(path)[1]

    def stripext(filename):
        if '.' in filename:
            return filename[:filename.rindex('.')]
        return filename

    def abspath(self,path):
        return os.path.join(self.config.config[config.BASEDIR],path)

    def strippath(self,path):
        if path.startswith(self.config.config[config.BASEDIR]):
            return path[len(self.config.config[config.BASEDIR])+1:]
        return path

    def sortFiles(self,files,fullpath=''):
        #sort alphabetically (case insensitive)
        sortedfiles = sorted(files,
                            key=lambda x : CherryModel.filename(x).upper() )
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
        results = self.cache.searchfor(term,maxresults=self.config.config[config.MAXSEARCHRESULTS])
        results = sorted(results,key=MatchOrder(term),reverse=True)
        results = results[:min(len(results),self.config.config[config.MAXSEARCHRESULTS])]
        ret = []
        for file in results:
            if os.path.isfile(os.path.join(self.config.config[config.BASEDIR],file)):
                ret.append(MusicEntry(self.strippath(file)))
            else:
                ret.append(MusicEntry(self.strippath(file),dir=True))
        return ret


class MusicEntry:
    def __init__(self, path, compact=False, dir=False, repr=None):
        self.path = path
        self.compact = compact
        self.dir = dir
        self.repr = repr

class JSON:
    def __init__(self):
        self.json = 'json'

    def render(self, musicentries):
        retlist = []
        for entry in musicentries:
            if entry.compact:
                retlist.append(self.pack(self.rendercompact(entry.path,entry.repr)))
            elif entry.dir:
                retlist.append(self.pack(self.renderdir(entry.path)))
            else:
                retlist.append(self.pack(self.renderfile(entry.path)))
        return self.pack(self.jsonlist(retlist),'results')

    def pack(self, content,mapto=None):
        if mapto == None:
            return '{'+content+'}'
        return '{"'+mapto+'" : '+content+'}'

    def renderfile(self, path):
        return '"type":"file", "path":"'+path+'"'

    def renderdir(self, path):
        return '"type":"dir", "path":"'+path+'"'

    def rendercompact(self, path):
        return '"type":"compact", "path":"'+path+'"'

    def jsonlist(self, list):
        return '['+', '.join(list)+']'


class HTML:
    def __init__(self, config):
        self.htmlhead = open('res/html/head.html').read()
        self.htmljplayer = open('res/html/jplayer.html').read()
        self.htmlplaylist = open('res/html/playlist.html').read()
        self.htmltail = open('res/html/tail.html').read()
        self.htmlsearchfield = open('res/html/searchfield.html').read()
        self.htmlsplitline = '<div class="splitline"></div>'
        self.config = config

    def render(self, musicentries):
        ret = ""
        for entry in musicentries:
            if entry.compact:
                ret += self.rendercompact(entry.path,entry.repr)
            elif entry.dir:
                ret += self.renderdir(entry.path)
            else:
                ret += self.renderfile(entry.path)
        return self.ulistify(ret)

    def wrapInsidePage(self, content):
        tabs = [self.tabify(self.rendersearchfield(),'search','Search'),
                self.tabify(self.htmlplaylist,'jplayer','Playlist'),
                self.tabify(self.divcontainer(content),'browser','Browser')]

        return  ' '.join([
                self.htmlhead,
                self.htmljplayer,
                self.renderTabs(tabs),
                self.htmltail
                ])
    def tabify(self, content, tabid, tabname):
        return ('<li><a class="'+tabid+'" href="#'+tabid+'">'+tabname+'</a></li>',
                '<div id="'+tabid+'">'+content+'</div>')

    def renderTabs(self, tabs):
        ret = '<div class="tabs"><ul class="tabNavigation">'
        for tab in tabs:
            ret += tab[0]
        ret += '</ul>'
        for tab in tabs:
            ret += tab[1]
        ret += '</div>'
        return ret







    def rendersearchfield(self):
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
        return self.htmlsearchfield.format(oneliner)

    def divcontainer(self,content):
        return '<div class="container">'+content+'</div>'

    def htmlfile(self,file,showfullpath=False):
        HOSTALIAS = config.config[config.HOSTALIAS]
        if showfullpath:
            simplename = file
        else:
            simplename = CherryModel.filename(file)
            urlpath = HOSTALIAS+'/'+file
            atitle = 'title="'+CherryModel.filename(file)+'"'
            ahref = 'href="javascript:;"'
            apath = ''
            cssclass = ''
            fullpathlabel = ''
            if file.lower().endswith(self.config.config[self.config.DOWNLOADABLE]):
                ahref = 'href="'+quote(urlpath)+'"'
            elif file.lower().endswith(self.config.config[self.config.PLAYABLE]):
                cssclass = ' class="mp3file" '
                apath = 'path="'+quote(urlpath)+'"'
                fullpathlabel = '<span class="fullpathlabel">'+CherryModel.filename(file,True)+'</span>'
            return '<a '+' '.join([atitle, ahref, apath, cssclass])+'>'+fullpathlabel+simplename+'</a>'
        return simplename

    def htmldir(self, dir,showfullpath=False):
        if showfullpath:
            return '<a dir="'+dir+'" href="javascript:;" class="listdir">'+dir+'</a>'
        else:
            return '<a dir="'+dir+'" href="javascript:;" class="listdir">'+CherryModel.filename(dir)+'</a>'

    def htmlcompact(self, filepath, filter):
        return '<a dir="'+filepath+'" filter="'+filter+'" href="javascript:;" class="compactlistdir">'+filter.upper()+'</a>'

    def ulistify(self,element):
        return '<ul>'+element+'</ul>'

    def listify(self,element,classes=[]):
        if classes == []:
            return '<li>'+element+'</li>'
        return '<li class="'+' '.join(classes)+'">'+element+'</li>'

    def renderfile(self, filepath, showfullpath=False):
        if showfullpath:
            return self.listify(self.htmlfile(filepath,True),['fileinlist'])
        else:
            return self.listify(self.htmlfile(filepath),['fileinlist'])

    def renderdir(self, filepath,showfullpath=False):
        if showfullpath:
            return self.listify(self.htmldir(filepath,True))
        else:
            return self.listify(self.htmldir(filepath))

    def rendercompact(self, filepath, filterletter):
        return self.listify(self.htmlcompact(filepath,filterletter))

    def rendersearch(self, results):
        ret = ""
        for result in results:
            if os.path.isdir(result):
                ret += self.renderdir(result,showfullpath=True)
            else:
                ret += self.renderfile(result,showfullpath=True)
        return self.ulistify(ret)

class Root(object):
    def __init__(self, config, model):
        self.model = model
        self.config = config
        self.html = HTML(config)
        self.json = JSON()

    def index(self, action='', value='', filter=''):
        if action=='search':
                if not value.strip():
                    return """<span style="width:100%; text-align: center; float: left;">if you're looking for nothing, you'll be getting nothing.</span>"""
                return self.html.render(self.model.search(value.strip()))
        else:
            dirtorender = value
            dirtorenderabspath = os.path.join(self.config.config[self.config.BASEDIR],value)
            if os.path.isdir(dirtorenderabspath):
                if action=='listdir':
                    return self.html.render(self.model.listdir(dirtorender))
                elif action=='compactlistdir':
                    return self.html.render(self.model.listdir(dirtorender,filter))
                else:
                    return self.html.wrapInsidePage(
                                self.html.render(self.model.listdir(dirtorender)) )
            else:
                return 'Error rendering dir [action: "'+action+'", value: "'+value+'"]'
    index.exposed = True

    def api(self, action='', value='', filter=''):
        if action=='search':
            return self.json.render(self.model.search(value.strip()))
        else:
            dirtorender = value
            dirtorenderabspath = os.path.join(self.config.config[self.config.BASEDIR],value)
            if os.path.isdir(dirtorenderabspath):
                if action=='listdir':
                    return self.html.render(self.model.listdir(dirtorender))
                elif action=='compactlistdir':
                    return self.html.render(self.model.listdir(dirtorender,filter))

    api.exposed = True

class Config:
    def __init__(self):
        self.BASEDIR = 'basedir'
        self.DOWNLOADABLE = 'downloadable'
        self.PLAYABLE = 'playable'
        self.HOSTALIAS = 'hostalias'
        self.MAXSHOWFOLDERS = 'maxshowfolders'
        self.CACHEENABLED = 'cacheenabled'
        self.MAXSEARCHRESULTS = 'maxsearchresults'
        self.USER = 'user'
        params = [
                self.BASEDIR,
                self.DOWNLOADABLE,
                self.PLAYABLE,
                self.MAXSHOWFOLDERS,
                self.CACHEENABLED,
                self.MAXSEARCHRESULTS,
                self.HOSTALIAS,
                self.USER
                ]
        confpath = 'config'
        conflines = open(confpath).readlines()
        self.config = {}
        for line in conflines:
            #remove newline and so on.
            line = line.strip()
            for param in params:
                self.parseconfigparam(line,param)
        if not self.BASEDIR in self.config:
            raise Exception('Please specify the BASEDIR variable in your config file.')
        self.splitparams(self.DOWNLOADABLE, tupleize=True)
        self.splitparams(self.PLAYABLE, tupleize=True)
        self.config[self.MAXSHOWFOLDERS] = int(self.config[self.MAXSHOWFOLDERS])
        self.config[self.MAXSEARCHRESULTS] = int(self.config[self.MAXSEARCHRESULTS])
        self.config[self.CACHEENABLED] = bool(self.config[self.CACHEENABLED])

    def parseconfigparam(self,line,param):
        #make sure each config param is not None
        if not param in self.config:
            self.config[param] = ''

        #set param if availbale
        if line.lower().startswith(param+'='):
            if param.lower() == self.USER.lower():
                #parse user credentials
                val = line[len(param+'='):].strip()

                if self.config[param] == '':
                    self.config[param] = {}
                pair = val.split(':')
                self.config[param][pair[0]] = pair[1]
                print('Added user '+pair[0])
            else:
                self.config[param] = line[len(param+'='):].strip()
                print(param+' set to '+self.config[param])

    def splitparams(self,param,tupleize=False,splitby=' ',isdict=False):
        if param in self.config:
            if isdict:
                pair = self.config[param].split(splitby)
                self.config[param][pair[0]] = pair[1]
            else:
                self.config[param] = self.config[param].split(splitby)
                if tupleize:
                    self.config[param] = tuple(self.config[param])


class MatchOrder:
    def __init__(self, searchword):
        self.fullsearchterm = searchword.lower()
        self.searchwords = searchword.lower().split(' ')
        self.perfectMatchBias = 100
        self.partialPerfectMatchBias = 20
        self.startsWithMatchBias = 1
        self.folderBonus = 5
    def __call__(self,file):
        fullpath = file.lower()
        file = CherryModel.filename(file).lower()
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

        file = CherryModel.stripext(file)
        #partial perfect match?
        for searchword in self.searchwords:
            if file == searchword:
                if os.path.isdir(fullpath):
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

config = Config()
import sqlitecache
#dircache = cache.Cache(config=config)
dircache = sqlitecache.SQLiteCache(config)
cherrymodel = CherryModel(config,dircache)
root = Root(config,cherrymodel)

def encrypt_pw(pw):
    #return hashlib.sha1(pw).hexdigest()
    return pw

def start(config):
    currentserverpath = os.path.abspath(os.path.dirname(__file__))

    cherrypy.config.update({
        'log.error_file': os.path.join(os.path.dirname(__file__), 'site.log'),
        'environment': 'production',
        "server.socket_host": "0.0.0.0",
        'server.socket_port': 8080, #TODO make port avaiable in config
        })
    cherrypy.tree.mount(root,'/',
        config={
            '/res': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': os.path.join(currentserverpath,'res'),
                'tools.staticdir.index': 'index.html',
            },
            '/'+config.config[config.HOSTALIAS]:{
                'tools.staticdir.on': True,
                'tools.staticdir.dir': config.config[config.BASEDIR],
                'tools.staticdir.index': 'index.html',
                'tools.encode.on' : True,
                'tools.encode.encoding' : 'utf-8',
            },
            '/': {
                'tools.basic_auth.on': True,
                'tools.basic_auth.realm': 'Cherry Music',
                'tools.basic_auth.users': config.config[config.USER],
                'tools.basic_auth.encrypt': encrypt_pw
            }

    })
    print('Starting server on port 8080 ...') #TODO display actually used port
    cherrypy.engine.start()


def serverless():
    cherrypy.server.unsubscribe()
    start(config)

def server():
    cherrypy.config.update({'log.screen': True})
    start(config)

if __name__ == "__main__":
    server()




"""echo '<div id="browser">';
	echo listdir();
	echo '</div>';
	echo '<div id="playlist-manager"><a class="save-playlist" href="javascript:;">Save current Playlist</a>';
	echo renderplaylistdir(PLAYLISTDIR);
	echo '</div>';
}"""



