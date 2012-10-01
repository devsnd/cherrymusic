#!/usr/bin/python3
import subprocess
import re
import os
from cherrymusicserver import log

READ_BUFFER = 1024*100
STREAM_BUFFER = 1024*50 #smaller than read buffer!
devnull = open(os.devnull,'w')

Encoders = {
    #encoders take input and write output from stdin and stout
    'ogg' : ['oggenc', '-'],
    'mp3': ['lame','-','-']
}

MimeTypes = {
    'mp3' : 'audio/mpeg',
    'ogg' : 'audio/ogg',
}

Decoders = {
    #filepath must be appendable!
    'mp3': ['mpg123', '-w', '-'],
    'ogg': ['oggdec', '-o', '-'],
    'flac' : ['flac', '-F','-d', '-c'],
    'aac' : ['faad', '-w'],        #untested
    
    #'fallback' : ['mplayer','-vc','null','-vo','null','-ao' 'pcm:waveheader:fast:file=-'],
}



def init():
    unavailEnc = []
    for k,v in Encoders.items():
        if not programAvailable(v[0]):
            unavailEnc.append((k,v[0]))
    for enc in unavailEnc:
        Encoders.pop(enc[0])
        log.i("Encoder '{}' not found. Will not be able to encode {} streams".format(enc[1], enc[0]))
    
    unavailDec = []
    for k,v in Decoders.items():
        if not programAvailable(v[0]):
            unavailDec.append((k,v[0]))
            
    for dec in unavailDec:
        Decoders.pop(dec[0])
        log.i("Decoder '{}' not found. Will not be able to encode {} streams".format(dec[1],dec[0]))
    
def programAvailable(name):
    try:
        subprocess.Popen([name],stdout=devnull, stderr=devnull)
        return True
    except OSError:
        return False

def filetype(filepath):
    if '.' in filepath:
        return filepath.lower()[filepath.rindex('.')+1:]
    return 'unknown filetype'

def decode(filepath):
    try:
        return subprocess.Popen(Decoders[filetype(filepath)]+[filepath], stdout=subprocess.PIPE, stderr=devnull)
    except OSError:
        log.w("Cannot decode {}, no decoder available, trying fallback decoder!".format(filepath))
        try:
            return subprocess.Popen(Decoders[filetype(filepath)]+[filepath], stdout=subprocess.PIPE, stderr=devnull)
        except OSError:
            log.w("Fallback failed, cannot decode {}!".format(filepath))
            raise

def encode(newformat, fromdecoder):
    try:
        return subprocess.Popen(Encoders[newformat], stdin=fromdecoder.stdout, stdout=subprocess.PIPE, stderr=devnull)
    except OSError:
        log.w("Cannot encode to {}, no encoder available!")
        raise

def transcode(filepath, newformat, usetmpfile=False):
    try:
        fromdecoder = decode(filepath)
        encoder = encode(newformat, fromdecoder)
        if usetmpfile:
            tmpfilename = re.sub('[^\w]','_',filepath)+'.'+newformat
            tmpfilepath = os.path.join('/tmp/',tmpfilename)
            tmpfilew = open(tmpfilepath,'wb')
            tmpfiler = open(tmpfilepath,'rb')
        while True:
            data = encoder.stdout.read(READ_BUFFER)
            if not data:
                break
            if usetmpfile:
                tmpfilew.write(data)
                yield tmpfiler.read(4096)
            else:
                yield data
    except OSError:
        log.w("Transcode of file '{}' to format '{}' failed!".format(filepath,newformat))

def getMimeType(format):
    return MimeTypes[format]
    
init()
