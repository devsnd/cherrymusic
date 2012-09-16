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

from cherrymusicserver import log
import os
import re
import sqlite3

from collections import deque
from operator import itemgetter
from time import time

import cherrymusicserver as cherry
from cherrymusicserver.util import timed, Progress

scanreportinterval = 1
AUTOSAVEINTERVAL = 100
debug = False
performanceTest = False
keepInRam = False

if debug:
    log.level(log.DEBUG)

class SQLiteCache(object):
    def __init__(self, DBFILENAME):
        setupDB = not os.path.isfile(DBFILENAME) or os.path.getsize(DBFILENAME) == 0
        setupDB |= DBFILENAME == ':memory:' #always rescan when using ram db.
        log.i('Starting database... ')

        self.conn = sqlite3.connect(DBFILENAME, check_same_thread=False)
        self.db = self.conn.cursor()
        self.rootDir = cherry.config.media.basedir.str

        if setupDB:
            log.i('Creating tables...')
            # Create table
            self.db.execute('CREATE TABLE files (parent int NOT NULL, filename text NOT NULL, filetype text, isdir int NOT NULL)')
            self.db.execute('CREATE TABLE dictionary (word text NOT NULL)')
            self.db.execute('CREATE TABLE search (drowid int NOT NULL, frowid int NOT NULL)')
            log.i('Creating index for dictionary and search tables... ')
            self.conn.execute('CREATE INDEX idx_dictionary ON dictionary(word)')
            self.conn.execute('CREATE INDEX idx_search ON search(drowid,frowid)')
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
        for fid, filename, ext in dbrootfilelist:
            dbrootfiledict[fid] = filename + ext
        dbrootfilelist = [] #free mem
        log.i('{} folders in db root'.format(len(dbrootfiledict)))
        try:
            realrootfiles = os.listdir(self.rootDir)
        except OSError:
            log.e('Cannot open "'+self.rootDir+'"!\nAre you sure you have set the right path in your configuration file?')
            exit(1)
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
            if cherry.config.search.autoupdate.bool \
                or 'y' == input("Changes detected ({} added, {} removed), perform rescan? (y/n)".format(len(addList), len(removeList))):
                if removeList:
                    self.remove_dead_file_entries(self.rootDir)
                if addList:
                    self.register_with_db(addList, basedir=self.rootDir)
        else:
            log.i('no changes found.')

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
            self.db.execute(sql, (term,))
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
                                    self.trim_to_maxlen(50, item.relpath)
                                    ))
        except Exception as exc:
            counter -= counter % AUTOSAVEINTERVAL
            if isinstance(exc, CriticalError):
                log.c(exc.msg)
                cherry.exitServer()
                exit(1)
            log.ex('')
            log.e("error while updating media: %s %s", exc.__class__.__name__, exc)
            log.e("rollback to previous commit.")
        else:
            progress.finish()
            log.i("media update complete.")
        finally:
            log.i("%d file records added", counter)


    def trim_to_maxlen(self, maxlen, s, insert=' ... '):
        '''no sanity check for maxlen and len(insert)'''
        if len(s) > maxlen:
            keep = maxlen - len(insert)
            left = keep // 2
            right = keep - left
            s = s[:left] + insert + s[-right:]
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
        self.conn.executemany('INSERT INTO search VALUES (?,?)',
                              ((wid, file_id) for wid in word_id_seq))


    def remove_dead_file_entries(self, rootpath):
        '''walk the media database and remove all entries which point
        to non-existent paths in the filesystem.'''
        root = File(rootpath, isdir=True)
        lister = self.db_recursive_filelister(root)
        lister.send(None)   # skip root
        for item in lister:
            if not item.exists:
                self.remove_recursive(item)


    def remove_recursive(self, fileobj):
        '''recursively remove fileobj and all its children from the media db.'''

        log.i('removing dead reference(s): %s "%s"',
              'directory' if fileobj.isdir else 'file',
              fileobj.relpath,
              )
        try:
            with self.conn:
                for item in self.db_recursive_filelister(fileobj):
                    self.remove_file(item)
        except Exception:
            log.e('error while removing dead reference(s)')
            log.e('rolled back to safe state.')
        else:
            log.i('done.')


    def remove_file(self, fileobj):
        '''removes a file entry from the db, which means removing: 
            - all search references,
            - all dictionary words which were orphaned by this,
            - the reference in the files table.'''
        try:
            dead_wordids = self.remove_from_search(fileobj.uid)
            self.remove_all_from_dictionary(dead_wordids)
            self.remove_from_files(fileobj.uid)
        except Exception as exception:
            log.ex(exception)
            log.e('error removing entry for %s', fileobj.relpath)
            raise exception


    def remove_from_search(self, fileid):
        '''remove all references to the given fileid from the search table.
        returns a list of all wordids which had their last search references
        deleted during this operation.'''
        foundlist = self.conn.execute(
                            'SELECT drowid FROM search' \
                            ' WHERE frowid=?', (fileid,)) \
                            .fetchall()
        wordset = set([t[0] for t in foundlist])

        self.conn.execute('DELETE FROM search WHERE frowid=?', (fileid,))

        for wid in set(wordset):
            count = self.conn.execute('SELECT count(*) FROM search'
                                      ' WHERE drowid=?', (wid,)) \
                                      .fetchone()[0]
            if count:
                wordset.remove(wid)
        return wordset


    def remove_all_from_dictionary(self, wordids):
        '''deletes all words with the given ids from the dictionary table'''
        if not wordids:
            return
        args = list(zip(wordids))
        self.conn.executemany('DELETE FROM dictionary WHERE rowid=(?)', args)


    def remove_from_files(self, fileid):
        '''deletes the given file id from the files table'''
        self.conn.execute('DELETE FROM files WHERE rowid=?', (fileid,))


    def db_recursive_filelister(self, fileobj):
        """generator: enumerates fileobj and children listed in the db as File 
        objects. each item is returned before children are fetched from db.
        this means that fileobj gets bounced back as the first return value."""
        queue = deque((fileobj,))
        while queue:
            item = queue.popleft()
            yield item
            queue.extend(self.fetch_child_files(item))


    def fetch_child_files(self, fileobj):
        '''fetches from files table a list of all File objects that have the
        argument fileobj as their parent.'''
        id_tuples = self.conn.execute(
                            'SELECT rowid, filename, filetype, isdir' \
                            ' FROM files where parent=?', (fileobj.uid,)) \
                            .fetchall()
        return [File(name + ext,
                     parent=fileobj,
                     isdir=False if isdir == 0 else True,
                     uid=uid) for uid, name, ext, isdir in id_tuples]


def perf(text=None):
    global __perftime
    if text == None:
        __perftime = time()
    else:
        log.d(text + ' took ' + str(time() - __perftime) + 's to execute')


class File():
    def __init__(self, path, parent=None, isdir=None, uid= -1):
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
        self.uid = uid
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
        '''this File's path relative to its root.basepath'''
        up = self.parent
        components = deque((self.basename,))
        while up is not None:
            components.appendleft(up.basename)
            up = up.parent
        return os.path.sep.join(components)

    @property
    def fullpath(self):
        '''this file's relpath with leading root.basepath'''
        return os.path.join(self.root.basepath, self.relpath)

    @property
    def name(self):
        '''if this file.isdir, its complete basename; otherwise its basename
        without extension suffix'''
        if self.isdir:
            name = self.basename
        else:
            name = os.path.splitext(self.basename)[0]
        return name

    @property
    def ext(self):
        '''if this file.isdir, the empty string; otherwise the extension suffix
        of its basename'''
        if self.isdir:
            ext = ''
        else:
            ext = os.path.splitext(self.basename)[1]
        return ext

    @property
    def exists(self):
        '''True if this file's fullpath exists in the filesystem'''
        return os.path.exists(self.fullpath)

    @property
    def islink(self):
        '''True if this file is a symbolic link'''
        return os.path.islink(self.fullpath)


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
        knownlinktargets = set()
        stack = deque()
        while(stack or paths):
            item = stack.pop() if stack else to_file(paths.pop())
            if item.islink:
                rp = os.path.realpath(item.fullpath)
                if rp in knownlinktargets:
                    raise CriticalError("Cyclic symlink found: " + item.relpath + " creates a circle if followed."
                                        " The program cannot handle this condition, and there are now likely"
                                        " duplicate entries in the media database. To fix, remove " +
                                        item.fullpath + " and restart the server.")
                if not item.parent is None:
                    log.e("Deeply nested symlink found: " + item.relpath +
                                    " All links must be directly in your basedir (" +
                                    os.path.abspath(basedir) + "). The program cannot"
                                    " safely handle them otherwise. Skipping.")
                    continue
                knownlinktargets.add(rp)
            if item.isdir:
                children = os.listdir(item.fullpath)
                if sort:
                    children = sorted(children, reverse=True) # reverse: append & pop happen at the end
                for name in children:
                    stack.append(File(name, parent=item))
            yield item


class CriticalError(Exception):
    '''
    An error that can not be handled and should result in program termination.
    '''
    def __init__(self, msg=None):
        self.msg = '' if msg is None else msg

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.msg)
