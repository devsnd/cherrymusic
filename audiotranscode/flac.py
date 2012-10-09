import subprocess
import os
import audiotranscode

devnull = open(os.devnull,'w')

formats = ['flac']

class LAME:
    def __init__(self):
        if not self.available():
            raise audiotranscode.TranscoderNotFound('flac')
        
    def encode(self, pcmDataPipe, newformat, bitrate=None):
        command = ['flac', '-c']
        enc = subprocess.Popen( audiotranscode.customizeCommand(command),
                                stdin=pcmDataPipe,
                                stdout=subprocess.PIPE,
                                stderr=devnull)
        return enc.stdout
        
    def decode(self, filePath):
        command = ['flac', '-F','-d', '-c', 'INFILE']
        dec = subprocess.Popen( audiotranscode.customizeCommand(command,infile=filePath),
                                stderr=devnull,
                                stdout=subprocess.PIPE)
        return dec.stdout

    def available():
        try:
            subprocess.Popen(['ffmpeg'],stdout=devnull, stderr=devnull)
            return True
        except OSError:
            return False