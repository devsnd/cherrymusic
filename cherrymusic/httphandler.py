"""This class provides the api to talk to the client.
It will then call the cherrymodel, to get the 
requested information"""

import os #shouldn't have to list any folder in the future!
import json

from cherrymusic import renderhtml
from cherrymusic import renderjson

class HTTPHandler(object):
    def __init__(self, config, model):
        self.model = model
        self.config = config
        self.html = renderhtml.HTML(config)
        self.jsonrenderer = renderjson.JSON(config)
        

    def index(self, action='', value='', filter=''):
        return open('res/main.html').read()
    index.exposed = True

    def api(self, action='', value='', filter=''):
        return self.handle(self.jsonrenderer, action, value, filter)
    api.exposed = True
    
    def handle(self, renderer, action, value, filter):
        if action=='search':
            if not value.strip():
                return """<span style="width:100%; text-align: center; float: left;">if you're looking for nothing, you'll be getting nothing.</span>"""
            return renderer.render(self.model.search(value.strip()))
        elif action == 'getmotd':
            return self.model.motd()
        elif action == 'saveplaylist':
            pl = json.loads(value)
            return self.model.savePlaylist(pl['playlist'],pl['playlistname']);
        elif action == 'loadplaylist':
            return json.dumps(self.model.loadPlaylist(playlistname=value));
        elif action == 'showplaylists':
            return json.dumps(self.model.showPlaylists());
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