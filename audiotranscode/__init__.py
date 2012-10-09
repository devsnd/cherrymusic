#!/usr/bin/python3
import subprocess
import re
import os
from cherrymusicserver import log
from cherrymusicserver import configuration
import tempfile

def customizeCommand(command, bitrate=192, infile=None):
    if 'BITRATE' in command:
        command[command.index('BITRATE')] = bitrate
    if 'INFILE' in command:
        command[command.index('INFILE')] = infile
    return command

Encoders = {
    #encoders take input and write output from stdin and stout
    'ogg' : ['oggenc', '-b','BITRATE_OGG','-'],
    'mp3' : ['lame','-b','BITRATE_MP3','-','-'],
    #'aac': ['faac','-o','-','-'], #doesn't work yet
}

#will sort available encoders depending on preference
encoderPreference = ["ogg","mp3","aac"]

MimeTypes = {
    'mp3' : 'audio/mpeg',
    'ogg' : 'audio/ogg',
}

Decoders = {
    #filepath must be appendable!
    'mp3'   : ['mpg123', '-w', '-'],
    'ogg'   : ['oggdec', '-o', '-'],
    'flac'  : ['flac', '-F','-d', '-c'],
    'aac'   : ['faad', '-w'],        #untested
    
    #'fallback' : ['mplayer','-vc','null','-vo','null','-ao' 'pcm:waveheader:fast:file=-'],
}

def sortByPref(elem):
    if elem in encoderPreference:
        return encoderPreference.index(elem)
    else:
        return len(encoderPreference)

def getEncoders():
    return sorted(list(Encoders.keys()),key=sortByPref)
    
def getDecoders():
    return list(Decoders.keys())


def init():
    unavailEnc = []
    for k,v in Encoders.items():
        if not programAvailable(v[0]):
            unavailEnc.append((k,v[0]))
        else:
            log.i("Encoder '{}' for format '{}' was found.".format(v[0],k))
    for enc in unavailEnc:
        Encoders.pop(enc[0])
        log.i("Encoder '{}' not found. Will not be able to encode {} streams".format(enc[1], enc[0]))
    
    unavailDec = []
    for k,v in Decoders.items():
        if not programAvailable(v[0]):
            unavailDec.append((k,v[0]))
        else:
            log.i("Decoder '{}' for format '{}' was found.".format(v[0],k))
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
            return subprocess.Popen(Decoders[filetype(filepath)]+[filepath], stdout=subprocess.PIPE)#, stderr=devnull)
        except OSError:
            log.w("Fallback failed, cannot decode {}!".format(filepath))
            raise

def encode(newformat, fromdecoder):
    try:
        enc = Encoders[newformat]
        if 'BITRATE_OGG' in enc:
            enc[enc.index('BITRATE_OGG')] = str(BITRATE_OGG)
        if 'BITRATE_MP3' in enc:
            enc[enc.index('BITRATE_MP3')] = str(BITRATE_MP3)
        return subprocess.Popen(enc, stdin=fromdecoder.stdout, stdout=subprocess.PIPE)#, stderr=devnull)
    except OSError:
        log.w("Cannot encode to {}, no encoder available!")
        raise

def estimateSize(filepath, newformat):
    return 4*1024*1024
    
def transcode(filepath, newformat):
    log.e("""Transcoding file {}
{} ---[{}]---> {}""".format(filepath,filetype(filepath),Encoders[newformat][0],newformat))
    try:
        fromdecoder = decode(filepath)
        encoder = encode(newformat, fromdecoder)
        while True:
            data = encoder.stdout.read(TRANSCODE_BUFFER)
            if not data:
                break               
            yield data
                    
    except OSError:
        log.w("Transcode of file '{}' to format '{}' failed!".format(filepath,newformat))
        
def getTranscoded(filepath, newformat, usetmpfile=False):
    needsTranscoding = True
    if usetmpfile:
        tmpfilepath = cache.createCacheFile(filepath,newformat)
        if cache.exists(filepath,newformat):
            yield open(tmpfilepath,'rb').read()
        else:
            tmpfilew = open(tmpfilepath,'wb')
            tmpfiler = open(tmpfilepath,'rb')
            for data in transcode(filepath,newformat):
                tmpfilew.write(data)
                #return as soon as enough data available
                if tmpfilew.tell()>tmpfiler.tell()+STREAM_BUFFER:
                    yield tmpfiler.read(STREAM_BUFFER) 
            yield tmpfiler.read() #return rest of file (encoding done)

    else:
        for data in transcode(filepath,newformat):
            yield data

def getMimeType(format):
    return MimeTypes[format]
    
class TranscodeCache:
    def __init__(self, maxTmpDirSizeMB = 50):
        self.maxTmpDirSizeBytes = maxTmpDirSizeMB*1024*1024
        self.tempdir = os.path.join(tempfile.gettempdir(),'.cherrymusic-cache')
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        self.cacheFiles = [CacheFile(os.path.join(self.tempdir,f)) for f in os.listdir(self.tempdir)]
    
    def getTmpFilePath(self,filepath,newformat):
        return os.path.join(self.tempdir,self.pathToFileName(filepath,newformat))
    
    def exists(self,filepath,newformat):
        exists = os.path.exists(self.getTmpFilePath(filepath,newformat)) 
        return exists and os.path.getsize(self.getTmpFilePath(filepath,newformat))>0
        
    def createCacheFile(self,filepath,newformat):
        self.checkQuotaAndDeleteOldest()
        tmpfile = self.getTmpFilePath(filepath,newformat)
        self.cacheFiles.append(CacheFile(tmpfile))
        return tmpfile
    
    def pathToFileName(self,filepath,newformat):
        return filepath.replace(os.sep,'_')+'.'+newformat
        
    def checkQuotaAndDeleteOldest(self):
        while(sum(map(lambda x:x.size, self.cacheFiles)) > self.maxTmpDirSizeBytes):
            self.cacheFiles = sorted(self.cacheFiles,key=lambda x:x.ctime)
            self.cacheFiles[0].delete()
            self.cacheFiles = self.cacheFiles[1:]
        for c in self.cacheFiles:
            c.update()
        
class CacheFile:
    def __init__(self, absfilepath):
        self.absfilepath = absfilepath
        self.update()
    
    def delete(self):
        os.remove(self.absfilepath)
               
    def update(self):
        try:
            self.ctime = os.path.getctime(self.absfilepath)
            self.size = os.path.getsize(self.absfilepath)
        except OSError:
            self.ctime = 0
            self.size = 0
        
TRANSCODE_BUFFER = 1024*200
STREAM_BUFFER = 1024*150 # < read buffer!
BITRATE_OGG = 160
BITRATE_MP3 = 192
devnull = open(os.devnull,'w')
cache = TranscodeCache()
init()