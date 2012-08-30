#!/usr/bin/python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

from cherrymusic import log
import os
import re
import sqlite3

from collections import deque
from operator import itemgetter
from time import time

import cherrymusic as cherry
from cherrymusic.util import timed, Progress, databaseFilePath

DEFAULT_CACHEFILE = databaseFilePath('cherry.cache.db') #set to ':memory:' to keep _everything_ in ram
scanreportinterval = 1
AUTOSAVEINTERVAL = 100
debug = False
performanceTest = False
keepInRam = False

class SQLiteCache(object):
    def __init__(self):
        DBFILENAME = databaseFilePath('cherry.cache.db')
        if not DBFILENAME:
            DBFILENAME = DEFAULT_CACHEFILE
        setupDB = not os.path.isfile(DBFILENAME) or os.path.getsize(DBFILENAME) == 0
        setupDB |= DBFILENAME == ':memory:' #always rescan when using ram db.
        log.i('Starting database... ')

        self.conn = sqlite3.connect(DBFILENAME, check_same_thread=False)
        self.db = self.conn.cursor()
        self.rootDir = cherry.config.media.basedir.str

        if setupDB:
            log.i('Creating tables...')
            # Create table
            self.db.execute('CREATE TABLE files (parent int, filename text, filetype text, isdir int)')
            self.db.execute('CREATE TABLE dictionary (word text)')
            self.db.execute('CREATE TABLE search (drowid int, frowid int)')
            log.i('Creating index for dictionary and search tables... ', end='')
            self.conn.execute('CREATE INDEX idx_dictionary ON dictionary(word)')
            self.conn.execute('CREATE INDEX idx_search ON search(drowid,frowid)');
            log.i('done.')
            log.i('Connected to Database. (' + DBFILENAME + ')')
        #I don't care about journaling!
        self.conn.execute('PRAGMA synchronous = OFF')
        self.conn.execute('PRAGMA journal_mode = MEMORY')
        self.checkIfRootUpdated()

    @timed
    def checkIfRootUpdated(self):
        log.i('Checking if root folder is up to date...')
        self.db.execute('''SELECT rowid, filename, filetype FROM files WHERE parent = -1''')
        dbrootfilelist = self.db.fetchall()
        dbrootfiledict = {}
        for id, filename, ext in dbrootfilelist:
            dbrootfiledict[id] = filename + ext
        dbrootfilelist = [] #free mem
        log.i('{} folders in db root'.format(len(dbrootfiledict)))
        realrootfiles = os.listdir(self.rootDir)
        log.i('{} folders in fs root'.format(len(realrootfiles)))
        log.i('Comparing db with filesystem...')

        removeList = [] #list of db ids
        addList = [] #list of file system paths

        for dbrootfile in dbrootfiledict.items():
            if not dbrootfile[1] in realrootfiles:
                removeList.append(dbrootfile[0])

        for realfile in realrootfiles:
            if realfile not in dbrootfiledict.values():
                addList.append(realfile)

        #addList = sorted(addList)
        #removeList = sorted(removeList)
        if len(removeList) > 0 or len(addList) > 0:
            if 'y' == input("Changes detected ({} added, {} removed), perform rescan? (y/n)".format(len(addList), len(removeList))):
                for removeItem in removeList:
                    log.i('removing file with id: ' + str(removeItem) + ' ...')
                    self.removeFromDB(removeItem)
                if addList:
                    self.register_with_db(addList, basedir=self.rootDir)
        else:
            log.i('no changes found.')

    def removeFromDB(self, filerowid):
        log.e("""removeFromDB: NOT IMPLEMENTED! should remove file """ + str(filerowid))

    @classmethod
    def searchterms(cls, searchterm):
        words = re.findall('(\w+)', searchterm.replace('_', ' '))
        return list(map(lambda x:x.lower(), words))

    @classmethod
    def splitext(cls, filename):
        if '.' in filename:
            dotindex = filename.rindex('.')
            return (filename[:dotindex], filename[dotindex:])
        return (filename, '')

    def fetchFileIds(self, terms):
        resultlist = []
        for term in terms:
            query = '''SELECT search.frowid FROM dictionary JOIN search ON search.drowid = dictionary.rowid WHERE dictionary.word = ?'''
            limit = ' LIMIT 0, 250' #TODO add maximum db results as configuration parameter
            log.d('Search term: ' + term)
            sql = query + limit
            if performanceTest:
                log.d('Query used: ' + sql)
            self.db.execute(sql, (term,));
            resultlist += self.db.fetchall()

        return resultlist

    def searchfor(self, value, maxresults=10):
        starttime = time()
        self.db = self.conn.cursor()
        terms = SQLiteCache.searchterms(value)
        if debug:
            log.d('searchterms')
            log.d(terms)
        results = []
        resultfileids = {}

        log.d('querying terms: ' + str(terms))
        perf()
        fileids = self.fetchFileIds(terms)
        perf('file id fetching')

        if debug:
            log.d('fileids')
            log.d(fileids)
        for fileid in fileids:
            if fileid in resultfileids:
                resultfileids[fileid] += 1
            else:
                resultfileids[fileid] = 1

        if debug:
            log.d('all file ids')
            log.d(resultfileids)
        #sort items by occurences and only return maxresults
        sortedresults = sorted(resultfileids.items(), key=itemgetter(1), reverse=True)
        #sortedresults = sortedresults[:min(len(resultfileids),maxresults)]
        if debug:
            log.d('sortedresults')
            log.d(sortedresults)
        bestresults = list(map(itemgetter(0), sortedresults))
        if debug:
            log.d('bestresults')
            log.d(bestresults)
        perf()
        for fileidtuple in bestresults:
            results.append(self.fullpath(fileidtuple[0]))
        perf('querying fullpaths')
        if debug:
            log.d('resulting paths')
            log.d(results)
        if performanceTest:
            log.d('overall search took ' + str(time() - starttime) + 's')
        return results

    def fullpath(self, filerowid):
        path = ''
        parent = None
        while(not parent == -1):
            cursor = self.conn.cursor()
            cursor.execute('''SELECT parent, filename, filetype FROM files WHERE rowid=? LIMIT 0,1''', (filerowid,))
            parent, filename, fileext = cursor.fetchone()
            path = os.path.join(filename + fileext, path)
            filerowid = parent
        return os.path.dirname(path)

    @timed
    def register_with_db(self, paths, basedir):
        """adds the given paths and their contents to the media database"""
        log.i("updating known media")
        counter = 0
        progress = Progress(len(paths))
        try:
            self.conn.isolation_level = "IMMEDIATE"  # instant writing lock, turn off autocommit
            with self.conn:                          # implicit commit, rollback on Exception
                for item in File.enumerate_files_in(paths, basedir=basedir, sort=True):
                    self.register_file_with_db(item)
                    counter += 1
                    if counter % AUTOSAVEINTERVAL == 0:
                        self.conn.commit()
                    if item.parent is None or item.parent.parent is None:
                        if item.parent is None:
                            progress.tick()
                        log.i(progress.formatstr(
                                    ' ETA %(eta)s (%(percent)s) -> ',
                                    self.trim_to_maxlen(50, self.path_from_basedir(item))
                                    ))
        except Exception as e:
            log.ex('')
            log.e("error while updating media: %s %s", e.__class__.__name__, e)
            log.e("rollback to previous commit.")
            counter -= counter % AUTOSAVEINTERVAL
        else:
            progress.finish()
            log.i("media update complete.")
        finally:
            log.i("%d file records added", counter)


    def path_from_basedir(self, fileobj):
        path = fileobj.name + fileobj.ext
        if not fileobj.parent is None:
            parentpath = self.path_from_basedir(fileobj.parent)
            path = os.path.join(parentpath, path)
        if fileobj.isdir:
            path += os.path.sep
        return path


    def trim_to_maxlen(self, maxlen, s, insert='...'):
        '''no sanity check for maxlen and len(insert)'''
        if len(s) > maxlen:
            split = (maxlen - len(insert)) // 2
            s = s[:split] + insert + s[-split:]
        return s


    def register_file_with_db(self, fileobj):
        """add data in File object to relevant tables in media database"""
        try:
            self.add_to_file_table(fileobj)
            word_ids = self.add_to_dictionary_table(fileobj.name)
            self.add_to_search_table(fileobj.uid, word_ids)
        except UnicodeEncodeError as e:
            log.e("wrong encoding for filename '%s' (%s)", fileobj.relpath, e.__class__.__name__)

    def add_to_file_table(self, fileobj):
        #files(parentid, filename, ext, 1 if isdir else 0)
        cursor = self.conn.execute('INSERT INTO files VALUES (?,?,?,?)', (fileobj.parent.uid if fileobj.parent else -1, fileobj.name, fileobj.ext, 1 if fileobj.isdir else 0))
        rowid = cursor.lastrowid
        fileobj.uid = rowid
        return [rowid]

    def add_to_dictionary_table(self, filename):
        word_ids = []
        for word in set(SQLiteCache.searchterms(filename)):
            wordrowid = self.conn.execute('''SELECT rowid FROM dictionary WHERE word = ? LIMIT 0,1''', (word,)).fetchone()
            if wordrowid is None:
                wordrowid = self.conn.execute('''INSERT INTO dictionary VALUES (?)''', (word,)).lastrowid
            else:
                wordrowid = wordrowid[0]
            word_ids.append(wordrowid)
        return word_ids

    def add_to_search_table(self, file_id, word_id_seq):
        self.conn.executemany('INSERT INTO search VALUES (?,?)', ((wid, file_id) for wid in word_id_seq))

def perf(text=None):
        global __perftime
        if text == None:
            __perftime = time()
        else:
            log.d(text + ' took ' + str(time() - __perftime) + 's to execute')

class File():
    def __init__(self, path, parent=None, isdir=None):
        if len(path) > 1:
            path = path.rstrip(os.path.sep)
        if parent is None:
            self.root = self
            self.basepath = os.path.dirname(path)
            self.basename = os.path.basename(path)
        else:
            if os.path.sep in path:
                raise ValueError('non-root filepaths must be direct relative to parent: path: %s, parent: %s' % (path, parent))
            self.root = parent.root
            self.basename = path
        self.uid = -1
        self.parent = parent
        if isdir is None:
            self.isdir = os.path.isdir(os.path.abspath(self.fullpath))
        else:
            self.isdir = isdir

    def __str__(self):
        return self.fullpath

    def __repr__(self):
        return ('%(fp)s%(isdir)s [%(n)s%(x)s] (%(id)s)%(pid)s' %
             {'fp': self.fullpath,
              'isdir': '/' if self.isdir else '',
              'n': self.name,
              'x': self.ext,
              'id': self.uid,
              'pid': ' -> ' + str(self.parent.uid) if self.parent and self.parent.uid > -1 else ''
              })

    @property
    def relpath(self):
        up = self.parent
        rp = deque((self.basename,))
        while up is not None:
            rp.appendleft(up.basename)
            up = up.parent
        return os.path.sep.join(rp)

    @property
    def fullpath(self):
        return os.path.join(self.root.basepath, self.relpath)

    @property
    def name(self):
        if self.isdir:
            name = self.basename
        else:
            name = os.path.splitext(self.basename)[0]
        return name

    @property
    def ext(self):
        if self.isdir:
            ext = ''
        else:
            ext = os.path.splitext(self.basename)[1]
        return ext


    @classmethod
    def enumerate_files_in(cls, paths, basedir=None, sort=False):
        """Takes a list of pathnames and turns them and their contents into
            File objects, iterating in a depth-first manner. If sort == True,
            items will turn up in the same order as they would when using the
            sorted(iterable) builtin."""
        if basedir is None:
            basedir = ''
        to_file = lambda name: File(os.path.join(basedir, name))
        if sort:
            paths = sorted(paths, reverse=True)  # reverse: append & pop happen at the end
        stack = deque()
        while(stack or paths):
            item = stack.pop() if stack else to_file(paths.pop())
            if item.isdir:
                children = os.listdir(item.fullpath)
                if sort:
                    children = sorted(children, reverse=True) # reverse: append & pop happen at the end
                for name in children:
                    stack.append(File(name, parent=item))
            yield item
