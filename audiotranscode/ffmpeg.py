import subprocess
import os
from audiotranscode import TranscoderNotFound

devnull = open(os.devnull,'w')

formats = ['mp3','ogg','aac','flac']

class FFMPEG:
    def __init__(self):
        if not self.available():
            raise TranscoderNotFound('ffmpeg')
        
    def encode(self, pcmDataPipe, newformat):
        enc = subprocess.Popen( ['ffmpeg','-i','pipe:0','-'],
                                stdin=pcmDataPipe,
                                stdout=subprocess.PIPE,
                                stderr=devnull)
        return enc.stdout
        
    def decode(self, filePath):
        dec = subprocess.Popen( ['ffmpeg', '-i', filename, '-f', 's16le', '-'],
                                stderr=devnull,
                                stdout=subprocess.PIPE)
        return dec.stdout

    def available():
        try:
            subprocess.Popen(['ffmpeg'],stdout=devnull, stderr=devnull)
            return True
        except OSError:
            return False