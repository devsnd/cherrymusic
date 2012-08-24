import os
from time import time
import sqlite3
import logging
from operator import itemgetter
import re

import cherrymusic as cherry
from cherrymusic.util import timed, Progress

DEFAULT_CACHEFILE = 'cherry.cache.db' #set to ':memory:' to keep _everything_ in ram
scanreportinterval = 1
AUTOSAVEINTERVAL = 100
debug = False
performanceTest = False
keepInRam = False

class SQLiteCache(object):
    def __init__(self):
        DBFILENAME = cherry.config.search.cachefile.str
        if not DBFILENAME:
            DBFILENAME = DEFAULT_CACHEFILE
        setupDB = not os.path.isfile(DBFILENAME) or os.path.getsize(DBFILENAME) == 0
        setupDB |= DBFILENAME == ':memory:' #always rescan when using ram db.
        print('Starting database... ')

        self.conn = sqlite3.connect(DBFILENAME, check_same_thread=False)
        self.db = self.conn.cursor()
        self.rootDir = cherry.config.media.basedir.str

        if setupDB:
            print('Creating tables...')
            # Create table
            self.db.execute('CREATE TABLE files (parent int, filename text, filetype text, isdir int)')
            self.db.execute('CREATE TABLE dictionary (word text)')
            self.db.execute('CREATE TABLE search (drowid int, frowid int)')
            print('Creating index for dictionary and search tables... ', end='')
            self.conn.execute('CREATE INDEX idx_dictionary ON dictionary(word)')
            self.conn.execute('CREATE INDEX idx_search ON search(drowid,frowid)');
            print('done.')
            print('Connected to Database. (' + DBFILENAME + ')')
        #I don't care about journaling!
        self.conn.execute('PRAGMA synchronous = OFF')
        self.conn.execute('PRAGMA journal_mode = MEMORY')
        self.checkIfRootUpdated()

    @timed
    def checkIfRootUpdated(self):
        print('Checking if root folder is up to date...')
        self.db.execute('''SELECT rowid, filename, filetype FROM files WHERE parent = -1''')
        dbrootfilelist = self.db.fetchall()
        dbrootfiledict = {}
        for id, filename, ext in dbrootfilelist:
            dbrootfiledict[id] = filename + ext
        dbrootfilelist = [] #free mem
        print('{} folders in db root'.format(len(dbrootfiledict)))
        realrootfiles = os.listdir(self.rootDir)
        print('{} folders in fs root'.format(len(realrootfiles)))
        print('Comparing db with filesystem...')

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
                    print('removing file with id: ' + str(removeItem) + ' ...')
                    self.removeFromDB(removeItem)

                self.register_with_db(addList, basedir=self.rootDir)
        else:
            print('no changes found.')

    def removeFromDB(self, filerowid):
        print("""removeFromDB: NOT IMPLEMENTED! should remove file """ + str(filerowid))

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
            print('Search term: ' + term)
            sql = query + limit
            if performanceTest:
                print('Query used: ' + sql)
            self.db.execute(sql, (term,));
            resultlist += self.db.fetchall()

        return resultlist

    def searchfor(self, value, maxresults=10):
        starttime = time()
        self.db = self.conn.cursor()
        terms = SQLiteCache.searchterms(value)
        if debug:
            print('searchterms')
            print(terms)
        results = []
        resultfileids = {}

        print('querying terms: ' + str(terms))
        perf()
        fileids = self.fetchFileIds(terms)
        perf('file id fetching')

        if debug:
            print('fileids')
            print(fileids)
        for fileid in fileids:
            if fileid in resultfileids:
                resultfileids[fileid] += 1
            else:
                resultfileids[fileid] = 1

        if debug:
            print('all file ids')
            print(resultfileids)
        #sort items by occurences and only return maxresults
        sortedresults = sorted(resultfileids.items(), key=itemgetter(1), reverse=True)
        #sortedresults = sortedresults[:min(len(resultfileids),maxresults)]
        if debug:
            print('sortedresults')
            print(sortedresults)
        bestresults = list(map(itemgetter(0), sortedresults))
        if debug:
            print('bestresults')
            print(bestresults)
        perf()
        for fileidtuple in bestresults:
            results.append(self.fullpath(fileidtuple[0]))
        perf('querying fullpaths')
        if debug:
            print('resulting paths')
            print(results)
        if performanceTest:
            print('overall search took ' + str(time() - starttime) + 's')
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
        logging.basicConfig(level=logging.DEBUG)
        logging.info("updating known media")
        counter = 0
        progress = Progress(len(paths))
        try:
            self.conn.isolation_level = "IMMEDIATE"  # instant writing lock, turn off autocommit
            with self.conn:                          # implicit commit, rollback on Exception
                for item in File.enumerate_files_in(paths, basedir=basedir, sort=True):
                    self.register_file_with_db(item)
                    counter += 1
                    if counter % AUTOSAVEINTERVAL == 0:
                        print('.', end='')
                        self.conn.commit()
                    if item.fullpath in paths:
                        progress.tick()
                        logging.debug('%s', progress.formatstr('ETA %(eta)s %(ticks)s / %(total)s (%(percent)s) | ', item.name))
        except Exception as e:
            logging.exception('')
            logging.error("error while updating media: %s %s", e.__class__.__name__, e)
            logging.error("rollback to previous commit.")
            counter -= counter % AUTOSAVEINTERVAL
        else:
            progress.finish()
            logging.info("media update complete.")
        finally:
            logging.info("%d file records added", counter)

    def register_file_with_db(self, fileobj):
        """add data in File object to relevant tables in media database"""
        try:
            self.add_to_file_table(fileobj)
            word_ids = self.add_to_dictionary_table(fileobj.name)
            self.add_to_search_table(fileobj.uid, word_ids)
        except UnicodeEncodeError as e:
            logging.error("wrong encoding for filename '%s' (%s)", fileobj.fullpath, e.__class__.__name__)
            raise e

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
            print(text + ' took ' + str(time() - __perftime) + 's to execute')

class File():
    def __init__(self, fullpath, parent=None, isdir=None):
        self.uid = -1
        self.name, self.ext = os.path.splitext(os.path.basename(fullpath))
        self.fullpath = fullpath
        self.parent = parent
        self.isdir = os.path.isdir(os.path.abspath(self.fullpath)) if isdir is None else isdir
        if self.isdir:
            self.name += self.ext
            self.ext = ''

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


    @classmethod
    def enumerate_files_in(cls, paths, basedir=None, sort=False):
        """Takes a list of pathnames and turns them and their contents into
            File objects, iterating in a depth-first manner. If sort == True,
            items will turn up in the same order as they would when using the
            sorted(iterable) builtin."""
        from collections import deque
        if basedir is None:
            basedir = ''
        if sort:
            paths = sorted(paths, reverse=True)  # reverse: append & pop happen at the end
        to_file = lambda name: File(os.path.join(basedir, name))
        stack = deque((to_file(d) for d in paths))
        while(len(stack) > 0):
            item = stack.pop()
            if item.isdir:
                children = os.listdir(item.fullpath)
                if sort:
                    children = sorted(children, reverse=True)
                for name in children:
                    fullpath = os.path.join(item.fullpath, name)
                    stack.append(File(fullpath, parent=item))
#            print(repr(item))
            yield item
