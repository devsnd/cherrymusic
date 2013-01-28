#!/usr/bin/python3

import urllib.request
import urllib.parse
import os.path
import codecs
import re
import subprocess
from unidecode import unidecode
from cherrymusicserver import log

class AlbumArtFetcher:
    def __init__(self,method='amazon', timeout=10):
        self.MAX_IMAGE_SIZE_BYTES = 100*1024
        self.IMAGE_SIZE = 80
        self.methods = {
            'amazon' : {
                'url' : "http://www.amazon.com/s/ref=sr_nr_i_0?rh=k:",
                'regex' : '<img  src="([^"]*)" class="productImage"'
            },
            'music.ovi.com' : {
                'url' : 'http://music.ovi.com/gb/en/pc/Search/?display=detail&text=',
                'regex': 'class="prod-sm"><img src="([^"]*)"',
                #improve image quality:
                'urltransformer' : lambda x : x[:x.rindex('/')]+'/?w=200&q=100',
            },
            'bestbuy.com':{
                'url' : 'http://www.bestbuy.com/site/searchpage.jsp?_dyncharset=ISO-8859-1&id=pcat17071&type=page&ks=960&sc=Global&cp=1&sp=&qp=crootcategoryid%23%23-1%23%23-1~~q6a616d657320626c616b65206a616d657320626c616b65~~nccat02001%23%230%23%23e&list=y&usc=All+Categories&nrp=15&iht=n&st=',
                'regex' : '<img itemprop="image" class="thumb" src="([^"]*)"'
            },
            'buy.com' : {
                'url' : "http://www.buy.com/sr/srajax.aspx?from=2&qu=",
                'regex' : ' class="productImageLink"><img src="([^"]*)"'
            },
        }
        if not method in self.methods:
            log.e('unknown album art fetch method: %s, using default.'%self.method)
            method = 'amazon'
        self.method = method
        self.timeout = timeout
        self.imageMagickAvailable = self.programAvailable('convert')
    
    def programAvailable(self,name):
        try:
            with open(os.devnull,'w') as devnull:
                subprocess.Popen([name],stdout=devnull, stderr=devnull)
                return True
        except OSError:
            return False
    
    def resize(self,imagepath,size):
        if self.imageMagickAvailable:
            with open(os.devnull,'w') as devnull:
                cmd = ['convert',imagepath,'-resize',str(size[0])+'x'+str(size[1]),'jpeg:-']
                print(' '.join(cmd))
                im = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                data = im.communicate()[0]
                header = {'Content-Type':"image/jpeg", 'Content-Length':len(data)}
                return header, data
        return None,''

    def fetch(self, searchterms, urlonly=False):
        searchterms = unidecode(searchterms).lower()
        searchterms = re.sub('[^a-z\s]','',searchterms)
        return self.fetchAlbumArt(self.methods[self.method], searchterms, urlonly)

    def retrieveData(self, url):
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19'
        urlhandler = urllib.request.urlopen(urllib.request.Request(url , headers={'User-Agent': user_agent}),timeout=self.timeout)
        return urlhandler.read(),urlhandler.info()

    def downloadImage(self, url):
        if url.startswith('//'):
            url = 'http:'+url
        raw_data, header = self.retrieveData(url)
        return header, raw_data

    def retrieveWebpage(self, url):
        return codecs.decode(self.retrieveData(url)[0],'UTF-8')

    def fetchAlbumArt(self, method, searchterm, urlonly=False):
        urlkeywords = urllib.parse.quote(searchterm)
        url = method['url']+urlkeywords
        #print(url)
        html = self.retrieveWebpage(url)
        matches = re.findall(method['regex'],html)
        if matches:
            if urlonly:
                return matches[0]
            else:
                imgurl = matches[0]
                if 'urltransformer' in method:
                    imgurl = method['urltransformer'](imgurl)
                return self.downloadImage(imgurl)
        else:
            if urlonly:
                return ''
            return None,''


    def fetchLocal(self, path):
        """ search a local path for image files.
        @param path: directory path
        @type path: string
        @return header, imagedata
        @rtype dict, bytestring"""

        filetypes = (".jpg", ".jpeg", ".png")
        for file_in_dir in os.listdir(path):
            if file_in_dir.lower().endswith(filetypes):
                try:
                    imgpath = os.path.join(path,file_in_dir)
                    if os.path.getsize(imgpath) > self.MAX_IMAGE_SIZE_BYTES:
                        return self.resize(imgpath,(self.IMAGE_SIZE,self.IMAGE_SIZE))
                    else:
                        with open(imgpath, "rb") as f:
                            data = f.read()
                            if(imgpath[-3:] == ".png"):
                                mimetype = "image/png"
                            else:
                                mimetype = "image/jpeg"
                            header = {'Content-Type':mimetype, 'Content-Length':len(data)}
                            return header, data
                except IOError:
                    return None, ''
        return None,''
