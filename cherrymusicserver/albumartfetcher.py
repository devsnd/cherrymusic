#!/usr/bin/python3

import urllib.request
import urllib.parse
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
        html = self.retrieveWebpage(url)   
        matches = re.findall(method['regex'],html)
        if matches:
            if urlonly:
                return matches[0]
            else:
                return self.downloadImage(matches[0])
        else:
            if urlonly:
                return ''
            return None,''
       
