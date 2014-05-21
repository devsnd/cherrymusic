#!/usr/bin/python3
import subprocess
import re
import os
import time

MimeTypes = {
    'mp3' : 'audio/mpeg',
    'ogg' : 'audio/ogg',
    'flac' : 'audio/flac',
    'aac' : 'audio/aac',
    'm4a' : 'audio/m4a',
    'wav' : 'audio/wav',
    'wma' : 'audio/x-ms-wma',
    'cue': '', # FIXME: What should we put here? .cue doesn't actually contain any audio.
}

class Transcoder(object):
    devnull = open(os.devnull,'w')
    
    def __init__(self, command):
        self.command = command
        
    def available(self):
        try:
            subprocess.Popen([self.command[0]],stdout=Transcoder.devnull, stderr=Transcoder.devnull)
            return True
        except OSError:
            return False

class Encoder(Transcoder):
    def __init__(self, filetype, command):
        Transcoder.__init__(self, command)
        self.filetype = filetype
        self.mimetype = MimeTypes[filetype]
        
    def encode(self, decoder_process, bitrate):
        cmd = self.command[:]
        if 'BITRATE' in cmd:
            cmd[cmd.index('BITRATE')] = '%dk' % bitrate
        return subprocess.Popen(cmd,
                                stdin=decoder_process.stdout,
                                stdout=subprocess.PIPE,
                                stderr=Transcoder.devnull
                                )
    
    def __str__(self):
        return "<Encoder type='%s' cmd='%s'>"%(self.filetype,str(' '.join(self.command)))

class Decoder(Transcoder):
    def __init__(self, filetype, command):
        Transcoder.__init__(self, command)
        self.filetype = filetype
        self.mimetype = MimeTypes[filetype]
        
    def decode(self, filepath, starttime=0, track=None):
        cmd = self.command[:]
        ext = os.path.splitext(filepath)[1]
        if ext == '.cue':
            if not track:
                track = 1
            else:
                track = int(track)
            from cherrymusicserver.cuesheet import Cuesheet
            cue = Cuesheet(filepath)
            audio_filepath = None
            for cdtext in cue.info[0].cdtext:
                if cdtext.type == 'FILE':
                    # Set the actual filepath from the FILE field
                    audio_filepath = os.path.join(os.path.dirname(filepath), cdtext.value[0])
                    break
            if audio_filepath is None or not os.path.exists(audio_filepath):
                raise DecodeError('Audiofile not found for cuesheet %s'%filepath)
            filepath = audio_filepath
            track_n = track
            track = cue.tracks[track-1]
            if 'STARTTIME' in cmd:
                cmd[cmd.index('STARTTIME')] = str(track.get_start_time())
            if 'LENGTH' in cmd:
                nexttrack = cue.get_next(track)
                if nexttrack:
                    track.nextstart = nexttrack.get_start_time()
                    cmd[cmd.index('LENGTH')] = str(track.get_length())
                else:
                    # Last track doesn't have a next track
                    # XXX: Actually we should remove the -t option altogether here
                    cmd[cmd.index('LENGTH')] = '99999'
        else:
            if 'STARTTIME' in cmd:
                hours, minutes, seconds = starttime//3600, starttime//60%60, starttime%60
                cmd[cmd.index('STARTTIME')] = '%d:%d:%d' % (hours, minutes, seconds)
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
        TranscodeError.__init__(self, value)

class DecodeError(TranscodeError):
    def __init__(self, value):
        TranscodeError.__init__(self, value)

class AudioTranscode:
    READ_BUFFER = 1024
    Encoders = [
        #encoders take input from stdin and write output to stout
        Encoder('ogg', ['oggenc', '-b','BITRATE','-']),
        Encoder('ogg', ['ffmpeg', '-i', '-', '-f', 'ogg', '-acodec', 'libvorbis', '-ab', 'BITRATE', '-']),
        Encoder('mp3', ['lame','-b','BITRATE','-','-']),
        Encoder('mp3', ['ffmpeg', '-i', '-', '-f', 'mp3', '-acodec', 'libmp3lame', '-ab', 'BITRATE', '-']),
        Encoder('aac', ['faac','-b','BITRATE','-P','-X','-o','-','-']),
        Encoder('m4a', ['faac','-b','BITRATE','-P','-X','-o','-','-']),
        Encoder('flac', ['flac', '--force-raw-format', '--endian=little', '--channels=2', '--bps=16', '--sample-rate=44100', '--sign=signed', '-o', '-', '-']),
        Encoder('wav', ['cat']),
        
    ]
    Decoders = [
        #filepath must be appendable!
        Decoder('mp3'  , ['mpg123', '-w', '-', 'INPUT']),
        Decoder('mp3'  , ['ffmpeg', '-ss', 'STARTTIME', '-i', 'INPUT', '-f', 'wav', '-acodec', 'pcm_s16le', '-']),
        Decoder('wma'  , ['ffmpeg', '-ss', 'STARTTIME', '-i', 'INPUT', '-f', 'wav', '-acodec', 'pcm_s16le', '-']),
        Decoder('ogg'  , ['oggdec', '-Q','-b', '16', '-o', '-', 'INPUT']),
        Decoder('ogg'  , ['ffmpeg', '-ss', 'STARTTIME', '-i', 'INPUT', '-f', 'wav', '-acodec', 'pcm_s16le', '-']),
        Decoder('flac' , ['flac', '-F','-d', '-c', 'INPUT']),
        Decoder('aac'  , ['faad', '-w', 'INPUT']), 
        Decoder('m4a'  , ['faad', '-w', 'INPUT']), 
        Decoder('wav'  , ['cat', 'INPUT']), 
        Decoder('cue'  , ['ffmpeg', '-ss', 'STARTTIME', '-t', 'LENGTH', '-i', 'INPUT', '-f', 'wav', '-']),
    ]
    
    def __init__(self,debug=False):
        self.debug = debug
        self.availableEncoders = list(filter(lambda x:x.available(),AudioTranscode.Encoders))
        self.availableDecoders = list(filter(lambda x:x.available(),AudioTranscode.Decoders))
        self.bitrate = {'mp3':160, 'ogg': 128, 'aac': 128}
    
    def availableEncoderFormats(self):
        return list(set(map(lambda x:x.filetype, self.availableEncoders)))
        
    def availableDecoderFormats(self):
        return list(set(map(lambda x:x.filetype, self.availableDecoders)))
    
    def _filetype(self, filepath):
        if '.' in filepath:
            return filepath.lower()[filepath.rindex('.')+1:]
    
    def _decode(self, filepath, decoder=None, starttime=0, track=None):
        if not os.path.exists(filepath):
            filepath = os.path.abspath(filepath)
            raise DecodeError('File not Found! Cannot decode "file" %s'%filepath)
        filetype = self._filetype(filepath)
        if not filetype in self.availableDecoderFormats():
            raise DecodeError('No decoder available to handle filetype %s'%filetype)
        elif not decoder:
            for d in self.availableDecoders:
                if d.filetype == filetype:
                    decoder = d
                    break
            if self.debug:
                print(decoder)
        return decoder.decode(filepath, starttime=starttime, track=track)
        
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
        audioformat = self._filetype(out_file)
        with open(out_file, 'wb') as fh:
            for data in self.transcodeStream(in_file,audioformat,bitrate):
                fh.write(data)
            fh.close()

    def transcodeStream(self, filepath, newformat, bitrate=None,
            encoder=None, decoder=None, starttime=0, track=None):
        decoder_process = None
        encoder_process = None
        try:
            decoder_process = self._decode(filepath, decoder, starttime=starttime, track=track)
            encoder_process = self._encode(newformat, decoder_process,bitrate=bitrate,encoder=encoder)
            while encoder_process.poll() == None:
                data = encoder_process.stdout.read(AudioTranscode.READ_BUFFER)
                if data == None:
                    time.sleep(0.1) #wait for new data...
                    break               
                yield data
        except Exception:
            #pass on exception, but clean up
            raise
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
        return MimeTypes.get(fileExtension)
