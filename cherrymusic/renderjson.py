"""
This class encapsulates all values returned by the cherrymodel
to be served as json to the client.
"""

import json

import cherrymusic as cherry
from cherrymusic import util 
from urllib.parse import quote

class JSON(object):

    def __init__(self):
        pass


    def render(self, musicentries):
        retlist = []
        for entry in musicentries:
            if entry.compact:
                #compact
                retlist.append({'type':'compact', 'urlpath':entry.path,'label':entry.repr})
            elif entry.dir:
                #dir
                simplename = util.filename(entry.path)
                retlist.append({'type':'dir', 'path':entry.path,'label':simplename})
            else:
                #file
                simplename = util.filename(entry.path)
                urlpath = quote('/' + cherry.config.server.hostalias.str + '/' + entry.path);
                retlist.append({'type':'file',
                                'urlpath':urlpath,
                                'path':entry.path,
                                'label':simplename})
        return json.dumps(retlist)
