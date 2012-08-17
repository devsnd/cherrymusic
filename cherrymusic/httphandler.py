"""This class provides the api to talk to the client.
It will then call the cherrymodel, to get the 
requested information"""

import os #shouldn't have to list any folder in the future!

from cherrymusic import renderhtml
from cherrymusic import renderjson

class HTTPHandler(object):
    def __init__(self, config, model):
        self.model = model
        self.config = config
        self.html = renderhtml.HTML(config)
        self.json = renderjson.JSON(config)
        

    def index(self, action='', value='', filter=''):
        return open('res/main.html').read()
        '''
        if action=='search':
                if not value.strip():
                    return """<span style="width:100%; text-align: center; float: left;">if you're looking for nothing, you'll be getting nothing.</span>"""
                return self.html.render(self.model.search(value.strip()))
        elif action == 'saveplaylist':
            self.model.saveplaylist(value)
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
        '''
    index.exposed = True

    def api(self, action='', value='', filter=''):
        return self.handle(self.json, action, value, filter)
    api.exposed = True
    
    def handle(self, renderer, action, value, filter):
        if action=='search':
            if not value.strip():
                return """<span style="width:100%; text-align: center; float: left;">if you're looking for nothing, you'll be getting nothing.</span>"""
            return renderer.render(self.model.search(value.strip()))
        elif action == 'saveplaylist':
            self.model.saveplaylist(value)
        elif action == 'getmotd':
            return self.model.motd()
        else:
            dirtorender = value
            dirtorenderabspath = os.path.join(self.config.config[self.config.BASEDIR],value)
            if os.path.isdir(dirtorenderabspath):
                if action=='compactlistdir':
                    return renderer.render(self.model.listdir(dirtorender,filter))
                else: #if action=='listdir':
                    return renderer.render(self.model.listdir(dirtorender))
            else:
                return 'Error rendering dir [action: "'+action+'", value: "'+value+'"]'