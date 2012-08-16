"""This class contains small static methods that
are used all over the place."""

import os

def filename(path,pathtofile=False):
    if pathtofile:
        return os.path.split(path)[0]
    else:
        return os.path.split(path)[1]
        
def stripext(filename):
    if '.' in filename:
        return filename[:filename.rindex('.')]
    return filename