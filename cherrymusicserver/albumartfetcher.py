#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
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

from tinytag import TinyTag

from cherrymusicserver import log

#unidecode is opt-dependency
try:
    from unidecode import unidecode
except ImportError:
    unidecode = lambda x: x

pillowAvailable = False
try:
    from PIL import Image
    from io import BytesIO
    pillowAvailable = True
except ImportError:
    pass


def programAvailable(name):
        """
        check if a program is available in the system PATH
        """
        try:
            with open(os.devnull, 'w') as devnull:
                process = subprocess.Popen([name], stdout=subprocess.PIPE,
                                           stderr=devnull)
                out, err = process.communicate()
                return 'ImageMagick' in codecs.decode(out, 'UTF-8')
        except OSError:
            return False

class AlbumArtFetcher:
    """
    provide the means to fetch images from different web services by
    searching for certain keywords
    """

    imageMagickAvailable = programAvailable('convert')

    methods = {
        'amazon': {
            'url': "http://www.amazon.com/s/?field-keywords=",
            'regexes': [
                '<img[^>]+?alt="Product Details"[^>]+?src="([^"]+)"',
                '<img[^>]+?src="([^"]+)"[^>]+?alt="Product Details"'],
        },
        'bestbuy.com': {
            'url': 'http://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&st=',
            'regexes': ['<div class="thumb".+?<img.+?src="([^"]+)"']
        },
        # buy.com is now rakuten.com
        # with a new search API that nobody bothered to figure out yet
        # 'buy.com': {
        #     'url': "http://www.buy.com/sr/srajax.aspx?from=2&qu=",
        #     'regexes': [' class="productImageLink"><img src="([^"]*)"']
        # },
    }

    def __init__(self, method='amazon', timeout=10):
        """define the urls of the services and a regex to fetch images
        """
        self.MAX_IMAGE_SIZE_BYTES = 100*1024
        self.IMAGE_SIZE = 80
        # the GET parameter value of the searchterm must be appendable
        # to the urls defined in "methods".
        if not method in self.methods:
            log.e(_(('''unknown album art fetch method: '%(method)s', '''
                     '''using default.''')),
                  {'method': method})
            method = 'google'
        self.method = method
        self.timeout = timeout

    def resize(self, imagepath, size):
        """
        resize an image using image magick or pillow

        Returns:
            the binary data of the image and a matching http header
        """
        with open(imagepath, 'rb') as fh:
            return self.resize_image_data(fh.read(), size)

    def resize_image_data(self, image_data, size):
        """
        resize an image as BytesIO using pillow or image magick

        Returns:
            the binary data of the image and a matching http header
        """
        if pillowAvailable:
            input_image = BytesIO()
            input_image.write(image_data)
            input_image.seek(0)
            image = Image.open(input_image)
            image.thumbnail(size, Image.ANTIALIAS)
            image_data = BytesIO()
            image.save(image_data, "JPEG")
            image_byte_count = image_data.tell()
            image_data.seek(0)
            return (
                {
                    'Content-Type': "image/jpeg",
                    'Content-Length': image_byte_count
                },
                image_data.read()
            )

        if AlbumArtFetcher.imageMagickAvailable:
            cmd = ['convert', '-',
                   '-resize', str(size[0])+'x'+str(size[1]),
                   'jpeg:-']
            im = subprocess.Popen(cmd,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            data, err = im.communicate(image_data)
            header = {'Content-Type': "image/jpeg",
                      'Content-Length': len(data)}
            return header, data
        return None, ''

        
        return None, ''


    def fetchurls(self, searchterm):
        """fetch image urls based on the provided searchterms

        Returns:
            list of urls
        """
        # choose the webservice to retrieve the images from
        method = self.methods[self.method]
        # use unidecode if it's available
        searchterm = unidecode(searchterm).lower()
        # make sure the searchterms are only letters and spaces
        searchterm = re.sub('[^a-z\s]', ' ', searchterm)
        # the keywords must always be appenable to the method-url
        url = method['url']+urllib.parse.quote(searchterm)
        #download the webpage and decode the data to utf-8
        html = codecs.decode(self.retrieveData(url)[0], 'UTF-8')
        # fetch all urls in the page
        matches = []
        for regex in method['regexes']:
            matches += re.findall(regex, html, re.DOTALL)
        return matches

    def fetch(self, searchterm):
        """
        fetch an image using the provided search term
        encode the searchterms and retrieve an image from one of the
        image providers

        Returns:
            an http header and binary data
        """
        matches = self.fetchurls(searchterm)
        if matches:
            imgurl = matches[0]
            if 'urltransformer' in self.method:
                imgurl = method['urltransformer'](imgurl)
            if imgurl.startswith('//'):
                imgurl = 'http:'+imgurl
            raw_data, header = self.retrieveData(imgurl)
            return header, raw_data
        else:
            return None, ''

    def retrieveData(self, url):
        """
        use a fake user agent to retrieve data from a webaddress

        Returns:
            the binary data and the http header of the request
        """
        user_agent = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 '
                      '(KHTML, like Gecko) Ubuntu/12.04 '
                      'Chromium/18.0.1025.168 Chrome/18.0.1025.168 '
                      'Safari/535.19')
        req = urllib.request.Request(url, headers={'User-Agent': user_agent})
        urlhandler = urllib.request.urlopen(req, timeout=self.timeout)
        return urlhandler.read(), urlhandler.info()

    def fetchLocal(self, path):
        """ search a local path for image files.
        @param path: directory path
        @type path: string
        @return header, imagedata, is_resized
        @rtype dict, bytestring"""
        fetchers = (self._fetch_folder_image, self._fetch_embedded_image)
        for fetcher in fetchers:
            header, data, resized = fetcher(path)
            if data:
                break
        return header, data, resized

    def _fetch_folder_image(self, path):
        filetypes = (".jpg", ".jpeg", ".png")
        try:
            for file_in_dir in sorted(os.listdir(path)):
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

    def _fetch_embedded_image(self, path):
        filetypes = ('.mp3',)
        max_tries = 3
        header, data, resized = None, '', False
        try:
            files = os.listdir(path)
            files = (f for f in files if f.lower().endswith(filetypes))
            for count, file_in_dir in enumerate(files, start=1):
                if count > max_tries:
                    break
                filepath = os.path.join(path, file_in_dir)
                try:
                    tag = TinyTag.get(filepath, image=True)
                    image_data = tag.get_image()
                except IOError:
                    continue
                if not image_data:
                    continue
                _header, _data = self.resize_image_data(
                    image_data, (self.IMAGE_SIZE, self.IMAGE_SIZE))
                if _data:
                    header, data, resized = _header, _data, True
                    break
        except OSError:
            pass
        return header, data, resized
