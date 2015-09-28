#!/usr/bin/python3
# 
from .mp3info import ID3v2Frame, ID3v1, ID3v2, MPEG, MP3Info

if __name__ == '__main__':
#    import sys
    i = MP3Info(open(sys.argv[1], 'rb'))
    print("File Info")
    print("---------")
    for key in i.__dict__.keys():
        print(key, ": ", i.__dict__[key])

    print
    print("MPEG Info")
    print("---------")
    for key in i.mpeg.__dict__.keys():
        print(key, ": ", i.mpeg.__dict__[key])

    print
    if not (i.id3 is None):
        print("ID3 Info")
        print("--------")
        for key in i.id3.__dict__.keys():
            print(key, ": ", i.id3.__dict__[key])
    else:
        print("No ID3 Info")
