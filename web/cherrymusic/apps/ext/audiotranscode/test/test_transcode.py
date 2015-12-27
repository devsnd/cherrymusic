#!/usr/bin/python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
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

import os
import tempfile

from nose.tools import *

import audiotranscode as transcode

transcoder = transcode.AudioTranscode(debug=True)
testdir = os.path.dirname(__file__)
testfiles = {
    'mp3' : os.path.join(testdir,'test.mp3'),
    'ogg' : os.path.join(testdir,'test.ogg'),
    'flac': os.path.join(testdir,'test.flac'),
    'wav': os.path.join(testdir,'test.wav'),
    'm4a': os.path.join(testdir,'test.m4a'),
    'wma': os.path.join(testdir,'test.wma'),
}
outputpath = tempfile.mkdtemp(prefix='test.audiotranscode.output.')

def generictestfunc(filepath, newformat, encoder, decoder):
    ident = "%s_%s_to_%s_%s" % (
            decoder.command[0],
            os.path.basename(filepath),
            encoder.command[0],
            newformat
        )
    outdata = b''
    for data in transcoder.transcode_stream(filepath, newformat, encoder=encoder, decoder=decoder):
        outdata += data
    ok_(len(outdata)>0, 'No data received: '+ident)
    with open(os.path.join(outputpath,ident+'.'+newformat),'wb') as outfile:
        outfile.write(outdata)


def test_generator():
    for enc in transcoder.Encoders:
        if not enc.available():
            print('Encoder %s not installed!'%enc.command[0])
            continue
        for dec in transcoder.Decoders:
            if not dec.available():
                print('Encoder %s not installed!'%dec.command[0])
                continue
            if dec.filetype in testfiles:
                yield generictestfunc, testfiles[dec.filetype], enc.filetype, enc, dec
