"""This class renders the html required for the response
to the client. It should be replaced asap by a simple json
api, so that the javascript renders the page."""

from urllib.parse import quote
from random import choice

from cherrymusic import util

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
        HOSTALIAS = self.config.config[self.config.HOSTALIAS]
        if showfullpath:
            simplename = file
        else:
            simplename = util.filename(file)
            urlpath = HOSTALIAS+'/'+file
            atitle = 'title="'+util.filename(file)+'"'
            ahref = 'href="javascript:;"'
            apath = ''
            cssclass = ''
            fullpathlabel = ''
            if file.lower().endswith(self.config.config[self.config.DOWNLOADABLE]):
                ahref = 'href="'+quote(urlpath)+'"'
            elif file.lower().endswith(self.config.config[self.config.PLAYABLE]):
                cssclass = ' class="mp3file" '
                apath = 'path="'+quote(urlpath)+'"'
                fullpathlabel = '<span class="fullpathlabel">'+util.filename(file,True)+'</span>'
            return '<a '+' '.join([atitle, ahref, apath, cssclass])+'>'+fullpathlabel+simplename+'</a>'
        return simplename

    def htmldir(self, dir,showfullpath=False):
        if showfullpath:
            return '<a dir="'+dir+'" href="javascript:;" class="listdir">'+dir+'</a>'
        else:
            return '<a dir="'+dir+'" href="javascript:;" class="listdir">'+util.filename(dir)+'</a>'

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










