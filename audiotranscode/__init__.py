#!/usr/bin/python3
import subprocess
import re
import os
import time

class Transcoder(object):
    devnull = open(os.devnull,'w')
    MimeTypes = {
        'mp3' : 'audio/mpeg',
        'ogg' : 'audio/ogg',
        'flac' : 'audio/flac',
        'aac' : 'audio/aac',
        'wav' : 'audio/wav',
    }
    def __init__(self):
        self.command = ['']
        
    def available(self):
        try:
            subprocess.Popen([self.command[0]],stdout=devnull, stderr=devnull)
            return True
        except OSError:
            return False

class Encoder(Transcoder):
    def __init__(self,filetype,command):
        self.filetype = filetype
        self.mimetype = Transcoder.MimeTypes[filetype]
        self.command = command
        
    def encode(self, decoder_process, bitrate):
        cmd = self.command[:]
        if 'BITRATE' in cmd:
            cmd[cmd.index('BITRATE')] = str(bitrate)
        return subprocess.Popen(cmd,
                                stdin=decoder_process.stdout,
                                stdout=subprocess.PIPE,
                                stderr=Transcoder.devnull
                                )
    
    def __str__(self):
        return "<Encoder type='%s' cmd='%s'>"%(self.filetype,str(' '.join(self.command)))

class Decoder(Transcoder):
    def __init__(self,filetype,command):
        self.filetype = filetype
        self.mimetype = Transcoder.MimeTypes[filetype]
        self.command = command        
        
    def decode(self, filepath):
        cmd = self.command[:]
        if 'INPUT' in cmd:
            cmd[cmd.index('INPUT')] = filepath
        return subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=Transcoder.devnull
                                )
        
    def __str__(self):
        return "<Decoder type='%s' cmd='%s'>"%(self.filetype,str(' '.join(self.command)))


class TranscodeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class EncodeError(TranscodeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class DecodeError(TranscodeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AudioTranscode:
    READ_BUFFER = 1024
    Encoders = [
        #encoders take input from stdin and write output to stout
        Encoder('ogg', ['oggenc', '-b','BITRATE','-']),
        #Encoder('ogg', ['ffmpeg', '-i', '-', '-f', 'ogg', '-acodec', 'vorbis', '-']), #doesn't work yet
        Encoder('mp3', ['lame','-b','BITRATE','-','-']),
        Encoder('mp3', ['ffmpeg', '-i', '-', '-f', 'mp3', '-acodec', 'libmp3lame', '-ab', 'BITRATE', '-']),
        Encoder('aac', ['faac','-b','BITRATE','-P','-X','-o','-','-']),
        Encoder('flac', ['flac', '--force-raw-format', '--endian=little', '--channels=2', '--bps=16', '--sample-rate=44100', '--sign=signed', '-o', '-', '-']),
        Encoder('wav', ['cat']),
        
    ]
    Decoders = [
        #filepath must be appendable!
        Decoder('mp3'  , ['mpg123', '-w', '-', 'INPUT']),
        Decoder('mp3'  , ['ffmpeg', '-i', 'INPUT', '-f', 'wav', '-acodec', 'pcm_s16le', '-']),
        Decoder('ogg'  , ['oggdec', '-Q','-b', '16', '-o', '-', 'INPUT']),
        Decoder('ogg'  , ['ffmpeg', '-i', 'INPUT', '-f', 'wav', '-acodec', 'pcm_s16le', '-']),
        Decoder('flac' , ['flac', '-F','-d', '-c', 'INPUT']),
        Decoder('aac'  , ['faad', '-w', 'INPUT']), 
        Decoder('wav'  , ['cat', 'INPUT']), 
    ]
    
    def __init__(self,debug=False):
        self.debug = debug
        self.availableEncoders = list(filter(lambda x:x.available,AudioTranscode.Encoders))
        self.availableDecoders = list(filter(lambda x:x.available,AudioTranscode.Decoders))
        self.bitrate = {'mp3':160, 'ogg': 128, 'aac': 128}
    
    def availableEncoderFormats(self):
        return list(set(map(lambda x:x.filetype, self.availableEncoders)))
        
    def availableDecoderFormats(self):
        return list(set(map(lambda x:x.filetype, self.availableDecoders)))
    
    def _filetype(filepath):
        if '.' in filepath:
            return filepath.lower()[filepath.rindex('.')+1:]
    
    def _decode(self, filepath, decoder=None):
        if not os.path.exists(filepath):
            filepath = os.path.abspath(filepath)
            raise DecodeError('File not Found! Cannot decode "file" %s'%filepath)
        filetype = AudioTranscode._filetype(filepath)
        if not filetype in self.availableDecoderFormats():
            raise DecodeError('No decoder available to handle filetype %s'%filetype)
        elif not decoder:
            for d in self.availableDecoders:
                if d.filetype == filetype:
                    decoder = d
                    break
            if self.debug:
                print(decoder)
        return decoder.decode(filepath)
        
    def _encode(self, audio_format, decoder_process, bitrate=None,encoder=None):
        if not audio_format in self.availableEncoderFormats():
            raise EncodeError('No encoder available to handle audio format %s'%audio_format)
        if not bitrate:
            bitrate = self.bitrate.get(audio_format)
        if not bitrate:
            bitrate = 128
        if not encoder:
            for e in self.availableEncoders:
                if e.filetype == audio_format:
                    encoder = e
                    break
            if self.debug:
                print(encoder)
        return encoder.encode(decoder_process, bitrate)

    def transcode(self, in_file, out_file, bitrate=None):
        print(out_file)
        audioformat = AudioTranscode._filetype(out_file)
        with open(out_file, 'wb') as fh:
            for data in self.transcodeStream(in_file,audioformat,bitrate):
                fh.write(data)
            fh.close()

    def transcodeStream(self, filepath, newformat,bitrate=None,encoder=None,decoder=None):
        decoder_process = None
        encoder_process = None
        try:
            decoder_process = self._decode(filepath, decoder)
            encoder_process = self._encode(newformat, decoder_process,bitrate=bitrate,encoder=encoder)
            while encoder_process.poll() == None:
                data = encoder_process.stdout.read(AudioTranscode.READ_BUFFER)
                if data == None:
                    time.sleep(0.1) #wait for new data...
                    break               
                yield data
        except Exception as e:
            #pass on exception, but clean up
            raise e
        finally:
            if decoder_process and decoder_process.poll() == None:
                if decoder_process.stderr:
                    decoder_process.stderr.close()
                if decoder_process.stdout:
                    decoder_process.stdout.close()
                if decoder_process.stdin:
                    decoder_process.stdin.close()
                decoder_process.terminate()
            if encoder_process:
                encoder_process.stdout.read()
                encoder_process.stdout.close()
                if encoder_process.stdin:
                    encoder_process.stdin.close()
                if encoder_process.stderr:
                    encoder_process.stderr.close()
                encoder_process.wait()
    
    def mimeType(self, fileExtension):
        return AudioTranscode.mimeType(fileExtension)
    
    def mimeType(fileExtension):
        return Transcoder.MimeTypes.get(fileExtension)
