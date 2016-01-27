
import codecs
import hashlib
import os

def album_art_file_path(directory_path):
    album_art_cache_path = os.path.join('/tmp', 'albumart')
    if not os.path.isdir(album_art_cache_path):
        os.makedirs(album_art_cache_path)
    if directory_path:
        filename = _md5_hash(directory_path) + '.thumb'
        album_art_cache_path = os.path.join(album_art_cache_path, filename)
    return album_art_cache_path

def _md5_hash(s):
    utf8_bytestr = codecs.encode(s, 'UTF-8')
    return hashlib.md5(utf8_bytestr).hexdigest()
