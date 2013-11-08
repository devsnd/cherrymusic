#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

try:
    import urllib.request
    import urllib.parse
except ImportError:
    import backport.urllib as urllib
import os.path
import codecs
import re
import subprocess
from cherrymusicserver import log

#unidecode is opt-dependency
try:
    from unidecode import unidecode
except ImportError:
    unidecode = lambda x: x


class AlbumArtFetcher:
    """
    provide the means to fetch images from different web services by
    searching for certain keywords
    """
    def __init__(self, method='amazon', timeout=10):
        """define the urls of the services and a regex to fetch images
        """
        self.MAX_IMAGE_SIZE_BYTES = 100*1024
        self.IMAGE_SIZE = 80
        # the GET parameter value of the searchterm must be appendable
        # to the urls defined in "methods".
        self.methods = {
            'amazon': {
                'url': "http://www.amazon.com/s/ref=sr_nr_i_0?rh=k:",
                'regex': '<img  src="([^"]*)" class="productImage"'
            },
            'music.ovi.com': {
                'url': 'http://music.ovi.com/gb/en/pc/Search/?display=detail&text=',
                'regex': 'class="prod-sm"><img src="([^"]*)"',
                #improve image quality:
                'urltransformer': lambda x: x[:x.rindex('/')]+'/?w=200&q=100',
            },
            'bestbuy.com': {
                'url': 'http://www.bestbuy.com/site/searchpage.jsp?_dyncharset=ISO-8859-1&id=pcat17071&type=page&ks=960&sc=Global&cp=1&sp=&qp=crootcategoryid%23%23-1%23%23-1~~q6a616d657320626c616b65206a616d657320626c616b65~~nccat02001%23%230%23%23e&list=y&usc=All+Categories&nrp=15&iht=n&st=',
                'regex': '<img itemprop="image" class="thumb" src="([^"]*)"'
            },
            'buy.com': {
                'url': "http://www.buy.com/sr/srajax.aspx?from=2&qu=",
                'regex': ' class="productImageLink"><img src="([^"]*)"'
            },
        }
        if not method in self.methods:
            log.e('unknown album art fetch method: %s, using default.'
                  % self.method)
            method = 'amazon'
        self.method = method
        self.timeout = timeout
        self.imageMagickAvailable = self.programAvailable('convert')

    def programAvailable(self, name):
        """
        check if a program is available in the system PATH
        """
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen([name], stdout=devnull, stderr=devnull)
                return True
        except OSError:
            return False

    def resize(self, imagepath, size):
        """
        resize an image using image magick

        Returns:
            the binary data of the image and a matching http header
        """
        if self.imageMagickAvailable:
            with open(os.devnull, 'w') as devnull:
                cmd = ['convert', imagepath,
                       '-resize', str(size[0])+'x'+str(size[1]),
                       'jpeg:-']
                print(' '.join(cmd))
                im = subprocess.Popen(cmd,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                data = im.communicate()[0]
                header = {'Content-Type': "image/jpeg",
                          'Content-Length': len(data)}
                return header, data
        return None, ''

    def fetch(self, searchterms, urlonly=False):
        """
        fetch an image using the provided search term

        Returns:
            an http header and binary data
        """
        searchterms = unidecode(searchterms).lower()
        searchterms = re.sub('[^a-z\s]', '', searchterms)
        return self.fetchAlbumArt(self.methods[self.method],
                                  searchterms, urlonly)

    def retrieveData(self, url):
        """
        use a fake user agent to retrieve data from a webaddress

        Returns:
            the binary data and the http header of the request
        """
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19'
        req = urllib.request.Request(url, headers={'User-Agent': user_agent})
        urlhandler = urllib.request.urlopen(req, timeout=self.timeout)
        return urlhandler.read(), urlhandler.info()

    def downloadImage(self, url):
        """
        downloads an image at the given url, puts the http protocol in
        the url if it was not specified

        Returns:
            a http header and the binary image data
        """
        if url.startswith('//'):
            url = 'http:'+url
        raw_data, header = self.retrieveData(url)
        return header, raw_data

    def retrieveWebpage(self, url):
        """
        download a webpage and decode the data to utf-8

        Returns:
            a string containing the HTML
        """
        return codecs.decode(self.retrieveData(url)[0], 'UTF-8')

    def fetchAlbumArt(self, method, searchterm, urlonly=False):
        """
        encode the searchterms and retrieve an image from one of the
        image providers

        Returns:
            a http header and the image as binary data
        """
        urlkeywords = urllib.parse.quote(searchterm)
        url = method['url']+urlkeywords
        #print(url)
        html = self.retrieveWebpage(url)
        matches = re.findall(method['regex'], html)
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
            return None, ''

    def fetchLocal(self, path):
        """ search a local path for image files.
        @param path: directory path
        @type path: string
        @return header, imagedata, is_resized
        @rtype dict, bytestring"""

        filetypes = (".jpg", ".jpeg", ".png")
        try:
            for file_in_dir in os.listdir(path):
                if not file_in_dir.lower().endswith(filetypes):
                    continue
                try:
                    imgpath = os.path.join(path, file_in_dir)
                    if os.path.getsize(imgpath) > self.MAX_IMAGE_SIZE_BYTES:
                        header, data = self.resize(imgpath,
                                                   (self.IMAGE_SIZE,
                                                    self.IMAGE_SIZE))
                        return header, data, True
                    else:
                        with open(imgpath, "rb") as f:
                            data = f.read()
                            if(imgpath.lower().endswith(".png")):
                                mimetype = "image/png"
                            else:
                                mimetype = "image/jpeg"
                            header = {'Content-Type': mimetype,
                                      'Content-Length': len(data)}
                            return header, data, False
                except IOError:
                    return None, '', False
        except OSError:
            return None, '', False
        return None, '', False
