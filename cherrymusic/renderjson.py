"""
bullshit: use the json module instead.
json.dumps(['list','of','things'])
"""

import json
from cherrymusic import util 
from urllib.parse import quote

class JSON(object):
    def __init__(self,config):
        self.config = config
    def render(self, musicentries):
        retlist = []
        for entry in musicentries:
            if entry.compact:
                retlist.append({'type':'compact', 'path':entry.path,'label':entry.repr})
                #retlist.append(self.pack(self.rendercompact(entry.path,entry.repr)))
            elif entry.dir:
                simplename = util.filename(entry.path)
                retlist.append({'type':'dir', 'path':entry.path,'label':simplename})
                #retlist.append(self.pack(self.renderdir(entry.path)))
            else:
                simplename = util.filename(entry.path)
                urlpath = quote('/'+self.config.config['hostalias']+'/'+entry.path);
                retlist.append({'type':'file',
                                'urlpath':urlpath,
                                'path':entry.path,
                                'label':simplename})
                #retlist.append(self.pack(self.renderfile(entry.path)))
        #return self.pack(self.jsonlist(retlist),'results')
        return json.dumps(retlist)