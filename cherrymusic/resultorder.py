"""This class determines the order of the results
fetched from the database by some mystic-voodoo-
hocuspocus heuristics"""

from cherrymusic import util
import os

class ResultOrder:
    def __init__(self, searchword):
        self.fullsearchterm = searchword.lower()
        self.searchwords = searchword.lower().split(' ')
        self.perfectMatchBias = 100
        self.partialPerfectMatchBias = 20
        self.startsWithMatchBias = 1
        self.folderBonus = 5
    def __call__(self,file):
        fullpath = file.lower()
        file = util.filename(file).lower()
        bias = 0


        #count occurences of searchwords
        occurences=0
        for searchword in self.searchwords:
            if searchword in fullpath:
                occurences += 3 #magic number for bias
            else:
                occurences -= 10
            if searchword in file:
                occurences += 10 #magic number for bias"""
            else:
                occurences -= 10

        bias += occurences

        #perfect match?
        if file == self.fullsearchterm or self.noThe(file) == self.fullsearchterm:
            return bias+self.perfectMatchBias

        file = util.stripext(file)
        #partial perfect match?
        for searchword in self.searchwords:
            if file == searchword:
                if os.path.isdir(fullpath):
                    bias += self.folderBonus
                return bias+self.partialPerfectMatchBias

        #file starts with match?
        for searchword in self.searchwords:
            if file.startswith(searchword):
                bias += self.startsWithMatchBias

        #remove possible track number
        while len(file)>0 and '0' <= file[0] and file[0] <= '9':
            file = file[1:]
        file = file.strip()
        for searchword in self.searchwords:
            if file == searchword:
                return bias + self.startsWithMatchBias

        return bias

    def noThe(self,a):
        if a.lower().endswith((', the',', die')):
            return a[:-5]
        return a