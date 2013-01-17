#!/usr/bin/python3

import urllib.request
import urllib.parse
import os.path
import glob
import codecs
import re
from unidecode import unidecode
from cherrymusicserver import log

class AlbumArtFetcher:
    def __init__(self,method='amazon', timeout=10):
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
        print(url)
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
        imglist = []
        filetypes = ["*.jpg", "*.jpeg", "*.png"]
        #get image files in directory
        for type in filetypes:
            searchpath = os.path.join(path, type)
            imglist.extend(glob.glob(searchpath))
        #check if images were found
        if(len(imglist) > 0):
            try:
                #get data
                file = open(imglist[0], "rb")
                data = file.read()
                #construct header
                mimetype = ""
                if(imglist[0][-3:] == ".png"):
                    mimetype = "images/png"
                else:
                    mimetype = "images/jpeg"
                header = {'Content-Type':mimetype, 'Content-Length':len(data)}
                file.close()
                return header, data
            except IOError:
                return None, ''
                 
        else:
            return None,''
