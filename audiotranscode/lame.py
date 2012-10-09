import subprocess
import os
import audiotranscode

devnull = open(os.devnull,'w')

formats = ['mp3']

class LAME:
    def __init__(self):
        if not self.available():
            raise audiotranscode.TranscoderNotFound('lame')
        
    def encode(self, pcmDataPipe, newformat, bitrate=192):
        command = ['lame','-b','BITRATE','-','-']
        enc = subprocess.Popen( audiotranscode.customizeCommand(command,bitrate=bitrate),
                                stdin=pcmDataPipe,
                                stdout=subprocess.PIPE,
                                stderr=devnull)
        return enc.stdout
        
    def decode(self, filePath):
        command = ['lame','--decode','INFILE','-']
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
