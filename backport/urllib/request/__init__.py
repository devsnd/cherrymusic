import urllib as ul

class Request:
    def __init__(self, url, data=None):
        self.url = url
        self.data = data

def urlopen(*args, **kwargs):
    print(args)
    print(kwargs)
    if len(args)>0 and isinstance(args[0], urllib.request.Request):
        r = args[0]
        return ul.urlopen(r.url,r.data)
    else:
        return ul.urlopen(args, kwargs)
