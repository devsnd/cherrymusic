"""
bullshit: use the json module instead.
json.dumps(['list','of','things'])
"""
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


