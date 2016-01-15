
import codecs
import hashlib
import os

def albumArtFilePath(directorypath):
    albumartcachepath = os.path.join('/tmp', 'albumart')
    if not os.path.exists(albumartcachepath):
        os.makedirs(albumartcachepath)
    if directorypath:
        filename = _md5_hash(directorypath) + '.thumb'
        albumartcachepath = os.path.join(albumartcachepath, filename)
    return albumartcachepath

def _md5_hash(s):
    utf8_bytestr = codecs.encode(s, 'UTF-8')
    return hashlib.md5(utf8_bytestr).hexdigest()
