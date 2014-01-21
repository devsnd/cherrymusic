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

CAPTURE_OUTPUT = True

# inject unavailable encoder
unavailable_enc = transcode.Encoder('mp3', ['notavailable'])
transcode.AudioTranscode.Encoders.append(unavailable_enc)

# inject unavailable decoder
unavailable_enc = transcode.Decoder('mp3', ['notavailable'])
transcode.AudioTranscode.Decoders.append(unavailable_enc)

transcoder = transcode.AudioTranscode(debug=True)
inputdir = os.path.dirname(__file__)
outputpath = tempfile.mkdtemp(prefix='test.cherrymusic.audiotranscode.')
testfiles = {
    'mp3': os.path.join(inputdir, 'test.mp3'),
    'ogg': os.path.join(inputdir, 'test.ogg'),
    'flac': os.path.join(inputdir, 'test.flac'),
    'wav': os.path.join(inputdir, 'test.wav'),
    'wma': os.path.join(inputdir, 'test.wma'),
}


def setup_module():
    if CAPTURE_OUTPUT:
        print('writing transcoder output to %r' % (outputpath,))


def teardown_module():
    if not CAPTURE_OUTPUT:
        os.rmdir(outputpath)


def generictestfunc(filepath, newformat, encoder, decoder):
    ident = "%s_%s_to_%s_%s" % (
            decoder.command[0],
            os.path.basename(filepath),
            encoder.command[0],
            newformat
    )
    #print(ident)
    outdata = b''
    transcoder_stream = transcoder.transcodeStream(
        filepath, newformat, encoder=encoder, decoder=decoder)
    for data in transcoder_stream:
        outdata += data
    if CAPTURE_OUTPUT:
        outname = os.path.join(outputpath, ident + '.' + newformat)
        with open(outname, 'wb') as outfile:
            outfile.write(outdata)
    ok_(len(outdata) > 0, 'No data received: ' + ident)


def test_generator():
    for enc in transcoder.Encoders:
        if not enc.available():
            print('Encoder %s not installed!' % (str(enc),))
            continue
        for dec in transcoder.Decoders:
            if not dec.available():
                print('Decoder %s not installed!' % (str(dec)))
                continue
            if dec.filetype in testfiles:
                filename = testfiles[dec.filetype]
                yield generictestfunc, filename, enc.filetype, enc, dec

@raises(transcode.DecodeError)
def test_file_not_found():
    try:
        for a in transcoder.transcodeStream('nosuchfile', 'mp3'):
            pass
    except Exception as e:
        #print exception for coverage
        print(e)
        raise

@raises(transcode.DecodeError)
def test_no_decoder_available():
    noaudio = os.path.join(inputdir,'test.noaudio')
    for a in transcoder.transcodeStream(noaudio, 'mp3'):
        pass

@raises(transcode.EncodeError)
def test_no_encoder_available():
    for a in transcoder.transcodeStream(testfiles['wav'], 'foobar'):
        pass

def test_automatically_find_encoder():
    for a in transcoder.transcodeStream(testfiles['wav'], 'wav'):
        pass

def test_transcode_file():
    outfile = os.path.join(outputpath, 'test_file.wav')
    transcoder.transcode(testfiles['wav'], outfile)

def test_mimetype():
    assert transcoder.mimeType('mp3') == 'audio/mpeg'