#!/usr/bin/python3
"""
audiotranscode
Copyright (c) 2013 Tom Wallroth

Sources on github:
  http://github.com/devsnd/audiotranscode/

licensed under GNU GPL version 3 (or later)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

__version__ = '0.2'

import subprocess
import os
import time
from distutils.spawn import find_executable

MIMETYPES = {
    'mp3': 'audio/mpeg',
    'ogg': 'audio/ogg',
    'oga': 'audio/ogg',
    'flac': 'audio/flac',
    'aac': 'audio/aac',
    'm4a': 'audio/m4a',
    'wav': 'audio/wav',
    'wma' : 'audio/x-ms-wma',
    'opus': 'audio/ogg; codecs=opus',
}


class Transcoder(object):
    """super class for encoders and decoders"""
    devnull = open(os.devnull, 'w')

    def __init__(self):
        self.command = ['']

    def available(self):
        """checks if the command defined in the encoder or decoder is
        available by calling it once"""
        return bool(find_executable(self.command[0]))


class Encoder(Transcoder):
    """encoder"""
    def __init__(self, filetype, command):
        Transcoder.__init__(self)
        self.filetype = filetype
        self.mimetype = MIMETYPES[filetype]
        self.command = command

    def encode(self, decoder_process, bitrate):
        """encodes the raw audio stream coming from the decoder_process
        using the spedcified command"""
        # get the absolute path under which the executable is found
        cmd = [find_executable(self.command[0])] + self.command[1:]
        if 'BITRATE' in cmd:
            cmd[cmd.index('BITRATE')] = str(bitrate)
        if 'KBITRATE' in cmd:
            cmd[cmd.index('KBITRATE')] = str(bitrate) + 'k'
        return subprocess.Popen(cmd,
                                stdin=decoder_process.stdout,
                                stdout=subprocess.PIPE,
                                stderr=Transcoder.devnull
                                )

    def __str__(self):
        return "<Encoder type='%s' cmd='%s'>" % (self.filetype,
                                                 str(' '.join(self.command)))

    def __repr__(self):
        return self.__str__()


class Decoder(Transcoder):
    """decoder"""
    def __init__(self, filetype, command):
        Transcoder.__init__(self)
        self.filetype = filetype
        self.mimetype = MIMETYPES[filetype]
        self.command = command

    def decode(self, filepath, starttime=0):
        """returns the process the decodes the file to a raw audio stream"""
        # get the absolute path under which the executable is found
        cmd = [find_executable(self.command[0])] + self.command[1:]
        if 'INPUT' in cmd:
            cmd[cmd.index('INPUT')] = filepath
        if 'STARTTIME' in cmd:
            hours, minutes, seconds = starttime//3600, starttime//60%60, starttime%60
            cmd[cmd.index('STARTTIME')] = '%d:%d:%d' % (hours, minutes, seconds)
        return subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=Transcoder.devnull
                                )

    def __str__(self):
        return "<Decoder type='%s' cmd='%s'>" % (self.filetype,
                                                 str(' '.join(self.command)))

    def __repr__(self):
        return self.__str__()


class TranscodeError(Exception):
    """exception for if either a decoder or encoder error has occurred"""
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        return repr(self.value)


class EncodeError(TranscodeError):
    """exception if an encoder is missing"""
    def __init__(self, value):
        TranscodeError.__init__(self, value)
        self.value = value

    def __str__(self):
        return repr(self.value)


class DecodeError(TranscodeError):
    """exception if a decoder is missing"""
    def __init__(self, value):
        TranscodeError.__init__(self, value)
        self.value = value

    def __str__(self):
        return repr(self.value)


def _filetype(filepath):
    """returns the file extension of a file"""
    if '.' in filepath:
        return filepath.lower()[filepath.rindex('.')+1:]


def mime_type(file_extension):
    """return a mimetype based on the file extension"""
    return MIMETYPES.get(file_extension)


class AudioTranscode:
    """main class that manages encoders and decoders
    call transcode(infile, outfile) for file transformations
    or transcode_stream to get a generator of the encoded stream"""
    READ_BUFFER = 1024
    Encoders = [
        # encoders take input from stdin and write output to stout
        # Encoder('ogg', ['ffmpeg', '-i', '-', '-f', 'ogg', '-c:a', 'libvorbis', '-b', 'KBITRATE', '-']),
        Encoder('ogg', ['oggenc', '--resample', '44100', '-b', 'BITRATE', '-']),
        Encoder('mp3', ['lame', '-b', 'BITRATE', '-', '-']),
        Encoder('aac', ['faac', '-b', 'BITRATE', '-P', '-X', '-o', '-', '-']),
        Encoder('m4a', ['faac', '-b', 'BITRATE', '-P', '-X', '-o', '-', '-']),
        Encoder('flac', ['flac', '--force-raw-format', '--endian=little',
                         '--channels=2', '--bps=16', '--sample-rate=44100',
                         '--sign=signed', '-o', '-', '-']),
        Encoder('wav', ['cat']),
        Encoder('opus', ['opusenc', '--bitrate', 'BITRATE', '--quiet',
                         '-', '-']),
    ]
    Decoders = [
        #INPUT is replaced with filepath
        Decoder('mp3', ['mpg123', '-w', '-', 'INPUT']),
        Decoder('mp3', ['ffmpeg', '-ss', 'STARTTIME',
	                '-i', 'INPUT', '-f', 'wav',
                        '-acodec', 'pcm_s16le', '-']),
        Decoder('wma', ['ffmpeg', '-ss', 'STARTTIME',
                        '-i', 'INPUT', '-f', 'wav',
                        '-acodec', 'pcm_s16le', '-']),
        Decoder('ogg', ['oggdec', '-Q', '-b', '16', '-o', '-', 'INPUT']),
        Decoder('ogg', ['ffmpeg',
                        '-ss', 'STARTTIME',
                        '-i', 'INPUT',
                        '-f', 'wav',
                        '-acodec', 'pcm_s16le',
                        '-']),
        # duplicate ogg decoders for oga files
        Decoder('oga', ['oggdec', '-Q', '-b', '16', '-o', '-', 'INPUT']),
        Decoder('oga', ['ffmpeg',
                        '-ss', 'STARTTIME',
                        '-i', 'INPUT',
                        '-f', 'wav',
                        '-acodec', 'pcm_s16le',
                        '-']),
        Decoder('flac', ['flac', '-F', '-d', '-c', 'INPUT']),
        Decoder('aac', ['faad', '-w', 'INPUT']),
        # prefer ffmpeg over faad for decoding to handle ALAC streams #584
        Decoder('m4a', ['ffmpeg', '-ss', 'STARTTIME',
                        '-i', 'INPUT', '-f', 'wav',
                        '-acodec', 'pcm_s16le', '-']),
        Decoder('m4a', ['faad', '-w', 'INPUT']),
        Decoder('wav', ['cat', 'INPUT']),
        Decoder('opus', ['opusdec', 'INPUT', '--force-wav', '--quiet', '-']),
    ]

    def __init__(self, debug=False):
        self.debug = debug
        self.available_encoders = [enc for enc in AudioTranscode.Encoders
                                   if enc.available()]
        self.available_decoders = [dec for dec in AudioTranscode.Decoders
                                   if dec.available()]
        self.bitrate = {'mp3': 160, 'ogg': 128, 'aac': 128, 'opus': '64'}

    def available_encoder_formats(self):
        """returns the names of all available encoder formats"""
        return set(enc.filetype for enc in self.available_encoders)

    def available_decoder_formats(self):
        """returns the names of all available decoder formats"""
        return set(dec.filetype for dec in self.available_decoders)

    def _decode(self, filepath, decoder=None, starttime=0):
        """find the correct decoder and return a decoder process"""
        if not os.path.exists(filepath):
            filepath = os.path.abspath(filepath)
            errmsg = 'File not Found! Cannot decode "file" %s'
            raise IOError(errmsg % filepath)
        filetype = _filetype(filepath)
        if not filetype in self.available_decoder_formats():
            errmsg = 'No decoder available to handle filetype %s'
            raise DecodeError(errmsg % filetype)
        elif not decoder:
            for dec in self.available_decoders:
                if dec.filetype == filetype:
                    decoder = dec
                    break
            if self.debug:
                print(decoder)
        return decoder.decode(filepath, starttime=starttime)

    def _encode(self, audio_format, decoder_process,
                bitrate=None, encoder=None):
        """find the correct encoder and pass in the decoder process,
        returns the encoder process"""
        if not bitrate:
            bitrate = self.bitrate.get(audio_format)
        if not bitrate:
            bitrate = 128
        if not encoder:
            for enc in self.available_encoders:
                if enc.filetype == audio_format:
                    encoder = enc
                    break
            if self.debug:
                print(encoder)
        return encoder.encode(decoder_process, bitrate)

    def check_encoder_available(self, audio_format):
        """checks if an encoder for this audio format is available"""
        if not audio_format in self.available_encoder_formats():
            errmsg = 'No encoder available to handle audio format %s'
            raise EncodeError(errmsg % audio_format)

    def transcode(self, in_file, out_file, bitrate=None):
        """transcodes one file into another format. the filetype is
        determined using the file extension of those files"""
        audioformat = _filetype(out_file)
        self.check_encoder_available(audioformat)
        with open(out_file, 'wb') as fhandler:
            for data in self.transcode_stream(in_file, audioformat, bitrate):
                fhandler.write(data)
            fhandler.close()

    def transcode_stream(self, filepath, newformat, bitrate=None,
                         encoder=None, decoder=None, starttime=0):
        """returns a generator wih the bytestream of the encoded audio
        stream"""
        if not encoder:
            self.check_encoder_available(newformat)
        decoder_process = None
        encoder_process = None
        try:
            decoder_process = self._decode(filepath, decoder,
	                                   starttime=starttime)
            encoder_process = self._encode(newformat, decoder_process,
                                           bitrate=bitrate, encoder=encoder)
            while encoder_process.poll() is None:
                data = encoder_process.stdout.read(AudioTranscode.READ_BUFFER)
                if data is None:
                    time.sleep(0.1)  # wait for new data...
                    break
                yield data
            yield encoder_process.stdout.read()
        finally:
            if decoder_process and decoder_process.poll() is None:
                if decoder_process.stderr:
                    decoder_process.stderr.close()
                if decoder_process.stdout:
                    decoder_process.stdout.close()
                if decoder_process.stdin:
                    decoder_process.stdin.close()
                decoder_process.terminate()
            if encoder_process:
                encoder_process.stdout.close()
                if encoder_process.stdin:
                    encoder_process.stdin.close()
                if encoder_process.stderr:
                    encoder_process.stderr.close()
                encoder_process.wait()
