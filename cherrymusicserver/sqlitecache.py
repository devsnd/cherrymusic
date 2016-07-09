#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
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

#python 2.6+ backward compability
from __future__ import unicode_literals

import os
import re
import sqlite3
import sys
import traceback

from collections import deque
from operator import itemgetter

import cherrymusicserver as cherry
from cherrymusicserver import database
from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver import util
from cherrymusicserver.cherrymodel import MusicEntry
from cherrymusicserver.database.connect import BoundConnector
from cherrymusicserver.util import Performance
from cherrymusicserver.progress import ProgressTree, ProgressReporter
import cherrymusicserver.tweak
from imp import reload
import random

from backport import unichr

UNIDECODE_AVAILABLE = True
try:
    import unidecode
except ImportError:
    UNIDECODE_AVAILABLE = False

scanreportinterval = 1
AUTOSAVEINTERVAL = 100
debug = False
keepInRam = False

#if debug:
#    log.level(log.DEBUG)

DBNAME = 'cherry.cache'

# unidecode will transform umlauts etc to their ASCII equivalent by
# stripping the accents. This is a simple table for other common
# transformations not performed by unidecode
SPECIAL_LETTER_TRANSFORMS = {
    'ä': 'ae',
    'ö': 'oe',
    'ü': 'ue',
}

class SQLiteCache(object):

    def __init__(self, connector=None):
        database.require(DBNAME, version='1')
        self.normalize_basedir()
        connector = BoundConnector(DBNAME, connector)
        self.DBFILENAME = connector.dblocation
        self.conn = connector.connection()
        self.db = self.conn.cursor()

        #I don't care about journaling!
        self.conn.execute('PRAGMA synchronous = OFF')
        self.conn.execute('PRAGMA journal_mode = MEMORY')
        self.load_db_to_memory()

    def file_db_in_memory(self):
        return not self.DBFILENAME == ':memory:' and cherry.config['search.load_file_db_into_memory']

    def load_db_to_memory(self):
        if self.file_db_in_memory():
            self.file_db_mem = MemoryDB(self.DBFILENAME, 'files')
            self.file_db_mem.db.execute('CREATE INDEX IF NOT EXISTS idx_files_parent'
                          ' ON files(parent)')

    @classmethod
    def searchterms(cls, searchterm):
        words = re.findall('(\w+|[^\s\w]+)',searchterm.replace('_', ' ').replace('%',' '),re.UNICODE)
        words = [word.lower() for word in words]
        if UNIDECODE_AVAILABLE:
            unidecoded = [unidecode.unidecode(word) for word in words]
            words += unidecoded
        special_transforms = []
        for word in words:
            if any(char in word for char in SPECIAL_LETTER_TRANSFORMS.keys()):
                for char, substitute in SPECIAL_LETTER_TRANSFORMS.items():
                    word = word.replace(char, substitute)
                special_transforms.append(word)
        words += special_transforms
        return set(words)

    def fetchFileIds(self, terms, maxFileIdsPerTerm, mode):
        """returns list of ids each packed in a tuple containing the id"""

        assert '' not in terms, _("terms must not contain ''")
        resultlist = []

        for term in terms:
            tprefix, tlast = term[:-1], term[-1]
            query = '''SELECT search.frowid FROM dictionary JOIN search ON search.drowid = dictionary.rowid WHERE '''
            if sys.maxunicode <= ord(tlast):
                where = ''' dictionary.word LIKE ? '''
                params = (term + '%',)
            else:
                where = ''' (dictionary.word >= ? AND dictionary.word < ?) '''
                nextchr = unichr(1 + ord(tlast))
                params = (term, tprefix + nextchr)
            order = ' ORDER BY dictionary.occurrences DESC '
            limit = ' LIMIT 0, ' + str(maxFileIdsPerTerm) #TODO add maximum db results as configuration parameter
            sql = query + where + order +limit
            if debug:
                log.d('Search term: %r', term)
                log.d('Query used: %r, %r', sql, params)
            #print(self.conn.execute('EXPLAIN QUERY PLAN ' + sql, params).fetchall())
            self.db.execute(sql, params)
            resultlist += self.db.fetchall()
        return resultlist

    def searchfor(self, value, maxresults=10):
        mode = 'normal'
        if value.startswith('!f '):
            mode = 'fileonly'
            value = value[3:]
        elif value.endswith(' !f'):
            mode = 'fileonly'
            value = value[:-3]
        elif value.startswith('!d '):
            mode = 'dironly'
            value = value[3:]
        elif value.endswith(' !d'):
            mode = 'dironly'
            value = value[:-3]

        reload(cherrymusicserver.tweak)
        file_search_limit = cherrymusicserver.tweak.SearchTweaks.normal_file_search_limit

        terms = SQLiteCache.searchterms(value)
        with Performance(_('searching for a maximum of %s files') % str(file_search_limit * len(terms))):
            if debug:
                log.d('searchterms')
                log.d(terms)
            results = []

            maxFileIdsPerTerm = file_search_limit
            with Performance(_('file id fetching')):
                #unpack tuples
                fileids = [t[0] for t in self.fetchFileIds(terms, maxFileIdsPerTerm, mode)]

            if len(fileids) > file_search_limit:
                with Performance(_('sorting results by fileid occurrences')):
                    resultfileids = {}
                    for fileid in fileids:
                        if fileid in resultfileids:
                            resultfileids[fileid] += 1
                        else:
                            resultfileids[fileid] = 1
                    # sort items by occurrences and only return maxresults
                    fileids = sorted(resultfileids.items(), key=itemgetter(1), reverse=True)
                    fileids = [t[0] for t in fileids]
                    fileids = fileids[:min(len(fileids), file_search_limit)]

            if mode == 'normal':
                with Performance(_('querying fullpaths for %s fileIds') % len(fileids)):
                    results += self.musicEntryFromFileIds(fileids)
            else:
                with Performance(_('querying fullpaths for %s fileIds, files only') % len(fileids)):
                    results += self.musicEntryFromFileIds(fileids,mode=mode)

            if debug:
                log.d('resulting paths')
                log.d(results)
            return results

    def listdir(self, path):
        basedir = cherry.config['media.basedir']
        targetpath = os.path.join(basedir, path)
        targetdir = self.db_find_file_by_path(targetpath)
        if targetdir is None:
            log.e(_('media cache cannot listdir %r: path not in database'), path)
            return []
        return list(map(lambda f: f.basename, self.fetch_child_files(targetdir)))

    def randomFileEntries(self, count):
        ''' Return a number of random entries from the file cache.

            The actual number returned may be less than ``count`` if the
            database does not contain enough entries or if randomization hits
            directory entries or entries that have been deleted.
        '''
        assert count >= 0
        cursor = self.conn.cursor()
        minId = cursor.execute('''SELECT _id FROM files ORDER BY _id ASC LIMIT 1;''').fetchone()
        if minId is None:
            return ()     # database is empty
        minId = minId[0]
        maxId = cursor.execute('''SELECT _id FROM files ORDER BY _id DESC LIMIT 1;''').fetchone()[0]

        if sys.version_info < (3,):
            genrange = xrange                   # use generator, not a large list
        else:
            genrange = range

        if maxId - minId < count:
            file_ids = genrange(minId, maxId + 1)
        else:
            # range generator pays off:
            file_ids = random.sample(genrange(minId, maxId + 1), count)

        entries = self.musicEntryFromFileIds(file_ids, mode='fileonly')
        random.shuffle(entries)
        return entries


    def musicEntryFromFileIds(self, filerowids, incompleteMusicEntries=None, mode='normal'):
        reload(cherrymusicserver.tweak)
        file_search_limit = cherrymusicserver.tweak.SearchTweaks.normal_file_search_limit

        #incompleteMusicEntries maps db parentid to incomplete musicEntry
        assert mode in ('normal', 'dironly', 'fileonly'), mode
        if incompleteMusicEntries is None:
            incompleteMusicEntries = {}
        musicEntries = [] #result list

        if self.file_db_in_memory():
            db = self.file_db_mem.db
        else:
            db = self.conn

        cursor = db.cursor()
        sqlquery = '''  SELECT rowid, parent, filename, filetype, isdir
                        FROM files WHERE rowid IN ({ids})'''.format(
                            ids=', '.join('?' * len(filerowids)))
        sqlparams = tuple(filerowids)

        if not incompleteMusicEntries:
            #only filter 1st recursion level
            if mode != 'normal':
                sqlquery += ' AND isdir = ?'
                sqlparams += ('dironly' == mode,)
            sqlquery += ' LIMIT 0, ?'
            sqlparams += (file_search_limit,)

        cursor.execute(sqlquery, sqlparams)
        for id, parent_id, filename, fileext, isdir in cursor.fetchall():
            path = filename + fileext
            #check if fetched row is parent of existing entry
            if id in incompleteMusicEntries:
                #remove item and map to new parent id
                entries = incompleteMusicEntries.pop(id)
                for entry in entries:
                    entry.path = os.path.join(path, entry.path)
            else:
                #id is not parent of any entry, so make a new one
                entries = [MusicEntry(path, dir=bool(isdir))]

            if parent_id == -1:
                #put entries in result list if they've reached top level
                musicEntries += entries
            else:
                #otherwise map parent id to dict
                incompleteMusicEntries[parent_id] = incompleteMusicEntries.get(parent_id,[]) + entries

        if incompleteMusicEntries:
            #recurse for all incomplete entries
            musicEntries += self.musicEntryFromFileIds(
                                incompleteMusicEntries.keys(),
                                incompleteMusicEntries = incompleteMusicEntries,
                                mode = mode
                            )
        return musicEntries

    def register_file_with_db(self, fileobj):
        """add data in File object to relevant tables in media database"""
        try:
            self.add_to_file_table(fileobj)
            word_ids = self.add_to_dictionary_table(fileobj.name)
            self.add_to_search_table(fileobj.uid, word_ids)
            return fileobj
        except UnicodeEncodeError as e:
            log.e(_("wrong encoding for filename '%s' (%s)"), fileobj.relpath, e.__class__.__name__)


    def add_to_file_table(self, fileobj):
        cursor = self.conn.execute('INSERT INTO files (parent, filename, filetype, isdir) VALUES (?,?,?,?)', (fileobj.parent.uid if fileobj.parent else -1, fileobj.name, fileobj.ext, 1 if fileobj.isdir else 0))
        rowid = cursor.lastrowid
        fileobj.uid = rowid
        return fileobj


    def add_to_dictionary_table(self, filename):
        word_ids = []
        for word in set(SQLiteCache.searchterms(filename)):
            wordrowid = self.conn.execute('''SELECT rowid FROM dictionary WHERE word = ? LIMIT 0,1''', (word,)).fetchone()
            if wordrowid is None:
                wordrowid = self.conn.execute('''INSERT INTO dictionary (word) VALUES (?)''', (word,)).lastrowid
            else:
                wordrowid = wordrowid[0]
            word_ids.append(wordrowid)
        return word_ids


    def add_to_search_table(self, file_id, word_id_seq):
        self.conn.executemany('INSERT INTO search (drowid, frowid) VALUES (?,?)',
                              ((wid, file_id) for wid in word_id_seq))


    def remove_recursive(self, fileobj, progress=None):
        '''recursively remove fileobj and all its children from the media db.'''


        if progress is None:
            log.i(
                  _('removing dead reference(s): %s "%s"'),
                  'directory' if fileobj.isdir else 'file',
                  fileobj.relpath,
                  )
            factory = None
            remove = lambda item: self.remove_file(item)
        else:
            def factory(new, pnt):
                if pnt is None:
                    return (new, None, progress)
                return (new, pnt, pnt[2].spawnchild('[-] ' + new.relpath))
            remove = lambda item: (self.remove_file(item[0]), item[2].tick())

        deld = 0
        try:
            with self.conn:
                for item in self.db_recursive_filelister(fileobj, factory):
                    remove(item)
                    deld += 1
        except Exception as e:
            log.e(_('error while removing dead reference(s): %s'), e)
            log.e(_('rolled back to safe state.'))
            return 0
        else:
            return deld


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
            log.e(_('error removing entry for %s'), fileobj.relpath)
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


    def db_recursive_filelister(self, fileobj, factory=None):
        """generator: enumerates fileobj and children listed in the db as File
        objects. each item is returned before children are fetched from db.
        this means that fileobj gets bounced back as the first return value."""
        if factory is None:
            queue = deque((fileobj,))
            while queue:
                item = queue.popleft()
                yield item
                queue.extend(self.fetch_child_files(item))
        else:
            queue = deque((factory(fileobj, None),))
            child = lambda parent: lambda item: factory(item, parent)
            while queue:
                item = queue.popleft()
                yield item
                queue.extend(map(child(item), self.fetch_child_files(item[0])))


    def fetch_child_files(self, fileobj, sort=True, reverse=False):
        '''fetches from files table a list of all File objects that have the
        argument fileobj as their parent.'''
        id_tuples = self.conn.execute(
                            'SELECT rowid, filename, filetype, isdir' \
                            ' FROM files where parent=?', (fileobj.uid,)) \
                            .fetchall()
        if sort:
            id_tuples = sorted(id_tuples, key=lambda t: t[1], reverse=reverse)
        return (File(name + ext,
                     parent=fileobj,
                     isdir=False if isdir == 0 else True,
                     uid=uid) for uid, name, ext, isdir in id_tuples)


    def normalize_basedir(self):
        basedir = cherry.config['media.basedir']
        basedir = os.path.normcase(basedir)
        if len(basedir) > 1:
            basedir = basedir.rstrip(os.path.sep)
        cherry.config = cherry.config.replace({'media.basedir': basedir})
        log.d(_('media base directory: %r') % basedir)


    @util.timed
    def full_update(self):
        '''verify complete media database against the filesystem and make
        necesary changes.'''

        log.i(_('running full update...'))
        try:
            self.update_db_recursive(cherry.config['media.basedir'], skipfirst=True)
        except:
            log.e(_('error during media update. database update incomplete.'))
        finally:
            self.update_word_occurrences()
            log.i(_('media database update complete.'))


    def partial_update(self, path, *paths):
        basedir = cherry.config['media.basedir']
        paths = (path,) + paths
        log.i(_('updating paths: %s') % (paths,))
        for path in paths:
            path = os.path.normcase(path)
            abspath = path if os.path.isabs(path) else os.path.join(basedir, path)
            normpath = os.path.normpath(abspath)
            if not normpath.startswith(basedir):
                log.e(_('path is not in basedir. skipping %r') % abspath)
                continue
            log.i(_('updating %r...') % path)
            try:
                self.update_db_recursive(normpath, skipfirst=False)
            except Exception as exception:
                log.e(_('update incomplete: %r'), exception)
        self.update_word_occurrences()
        log.i(_('done updating paths.'))


    def update_db_recursive(self, fullpath, skipfirst=False):
        '''recursively update the media database for a path in basedir'''

        from collections import namedtuple
        Item = namedtuple('Item', 'infs indb parent progress')
        def factory(fs, db, parent):
            fileobj = fs if fs is not None else db
            name = fileobj.relpath or fileobj.fullpath if fileobj else '<path not found in filesystem or database>'
            if parent is None:
                progress = ProgressTree(name=name)
                maxlen = lambda s: util.trim_to_maxlen(50, s)
                progress.reporter = ProgressReporter(lvl=1, namefmt=maxlen)
            else:
                progress = parent.progress.spawnchild(name)
            return Item(fs, db, parent, progress)

        log.d(_('recursive update for %s'), fullpath)
        generator = self.enumerate_fs_with_db(fullpath, itemfactory=factory)
        skipfirst and generator.send(None)
        adds_without_commit = 0
        add = 0
        deld = 0
        try:
            with self.conn:
                for item in generator:
                    infs, indb, progress = (item.infs, item.indb, item.progress)
                    if infs and indb:
                        if infs.isdir != indb.isdir:
                            progress.name = '[±] ' + progress.name
                            deld += self.remove_recursive(indb, progress)
                            self.register_file_with_db(infs)
                            adds_without_commit = 1
                        else:
                            infs.uid = indb.uid
                            progress.name = '[=] ' + progress.name
                    elif indb:
                        progress.name = '[-] ' + progress.name
                        deld += self.remove_recursive(indb, progress)
                        adds_without_commit = 0
                        continue    # progress ticked by remove; don't tick again
                    elif infs:
                        self.register_file_with_db(item.infs)
                        adds_without_commit += 1
                        progress.name = '[+] ' + progress.name
                    else:
                        progress.name = '[?] ' + progress.name
                    if adds_without_commit == AUTOSAVEINTERVAL:
                        self.conn.commit()
                        add += adds_without_commit
                        adds_without_commit = 0
                    progress.tick()
        except Exception as exc:
            log.e(_("error while updating media: %s %s"), exc.__class__.__name__, exc)
            log.e(_("rollback to previous commit."))
            traceback.print_exc()
            raise exc
        finally:
            add += adds_without_commit
            log.i(_('items added %d, removed %d'), add, deld)
            self.load_db_to_memory()

    def update_word_occurrences(self):
        log.i(_('updating word occurrences...'))
        self.conn.execute('''UPDATE dictionary SET occurrences = (
                select count(*) from search WHERE search.drowid = dictionary.rowid
            )''')

    def enumerate_fs_with_db(self, startpath, itemfactory=None):
        '''
        Starting at `startpath`, enumerates path items containing representations
        for each path as it exists in the filesystem and the database,
        respectively.

        `startpath` and `basedir` need to be absolute paths, with `startpath`
        being a subtree of `basedir`. However, no checks are being promised to
        enforce the latter requirement.

        Iteration is depth-first, but each path is returned before its children
        are determined, to enable recursive corrective action like deleting a
        whole directory from the database at once. Accordingly, the first item
        to be returned will represent `startpath`. This item is guaranteed to be
        returned, even if `startpath` does not exist in filesystem and database;
        all other items will have at least one existing representation.

        `basedir`, should it happen to equal `startpath`, will be returned as an
        item. It is up to the caller to properly deal with it.

        Each item has the following attributes: `infs`, a File object
        representing the path in the filesystem; `indb`, a File object
        representing the path in the database; and `parent`, the parent item.
        All three can be None, signifying non-existence.

        It is possible to customize item creation by providing an `itemfactory`.
        The argument must be a callable with the following parameter signature::

            itemfactory(infs, indb, parent [, optional arguments])

        and must return an object satisfying the above requirements for an item.
        '''
        from backport.collections import OrderedDict
        basedir = cherry.config['media.basedir']
        startpath = os.path.normcase(startpath).rstrip(os.path.sep)
        Item = itemfactory
        if Item is None:
            from collections import namedtuple
            Item = namedtuple('Item', 'infs indb parent')
        assert os.path.isabs(startpath), _('argument must be an abolute path: "%s"') % startpath
        assert startpath.startswith(basedir), _('argument must be a path in basedir (%s): "%s"') % (basedir, startpath)

        if not os.path.exists(startpath):
            fsobj = None
        elif startpath == basedir:
            fsobj = File(basedir)
        elif startpath > basedir:
            pathparent, pathbase = os.path.split(startpath)
            fsparent = self.db_find_file_by_path(pathparent, create=True)
            assert fsparent is not None, _('parent path not in database: %r') % pathparent
            fsobj = File(pathbase, fsparent)
            del pathparent, pathbase, fsparent
        else:
            assert False, _("shouldn't get here! (argument path not in basedir)")

        dbobj = self.db_find_file_by_path(startpath)
        stack = deque()
        stack.append(Item(fsobj, dbobj, None))
        while stack:
            item = stack.pop()
            yield item
            dbchildren = {}
            if item.indb:
                dbchildren = OrderedDict((
                                   (f.basename, f)
                                   for f in self.fetch_child_files(item.indb)
                                   ))
            if item.infs and item.infs.isdir:
                for fs_child in File.inputfilter(item.infs.children()):
                    db_child = dbchildren.pop(fs_child.basename, None)
                    stack.append(Item(fs_child, db_child, item))
            for db_child in dbchildren.values():
                stack.append(Item(None, db_child, item))
            del dbchildren


    def db_find_file_by_path(self, fullpath, create=False):
        '''Finds an absolute path in the file database. If found, returns
        a File object matching the database record; otherwise, returns None.
        Paths matching a media basedir are a special case: these will yield a
        File object with an invalid record id matching the one listed by its
        children.
        '''
        basedir = cherry.config['media.basedir']
        fullpath = os.path.normpath(fullpath)
        if os.path.isabs(fullpath):
            if not fullpath.startswith(basedir):
                return None
        else:
            fullpath = os.path.join(basedir, fullpath)

        relpath = fullpath[len(basedir):].strip(os.path.sep)
        root = File(basedir, isdir=True, uid= -1)
        if not relpath:
            return root

        file = root
        for part in relpath.split(os.path.sep):
            found = False
            for child in self.fetch_child_files(file):  # gotta be ugly: don't know if name/ext split in db
                if part == child.basename:
                    found = True
                    file = child
                    break
            if not found:
                if create:
                    file = File(part, parent=file)
                    log.i(_('creating database entry for %r'), file.relpath)
                    self.register_file_with_db(file)
                else:
                    return None
        return file


if sys.version_info < (3,):
    from codecs import decode
    encoding = sys.getfilesystemencoding()
    is_unicode = lambda s: isinstance(s, type(''))  # from unicode_literals import

    def _unicode_listdir(dirname):
        for name in os.listdir(dirname):
            try:
                yield (name if is_unicode(name) else decode(name, encoding))
            except UnicodeError:
                log.e(_('unable to decode filename %r in %r; skipping.'),
                    name, dirname)
else:
    _unicode_listdir = os.listdir


class File():
    def __init__(self, path, parent=None, isdir=None, uid= -1):
        assert isinstance(path, type('')), _('expecting unicode path, got %s') % type(path)

        if len(path) > 1:
            path = path.rstrip(os.path.sep)
        if parent is None:
            self.root = self
            self.basepath = os.path.dirname(path)
            self.basename = os.path.basename(path)
        else:
            if os.path.sep in path:
                raise ValueError(_('non-root filepaths must be direct relative to parent: path: %s, parent: %s') % (path, parent))
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
        '''this File's path relative to its root'''
        up = self
        components = deque()
        while up != self.root:
            components.appendleft(up.basename)
            up = up.parent
        return os.path.sep.join(components)

    @property
    def fullpath(self):
        '''this file's relpath with leading root path'''
        fp = os.path.join(self.root.basepath, self.root.basename, self.relpath)
        if len(fp) > 1:
            fp = fp.rstrip(os.path.sep)
        return fp

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

    def children(self, sort=True, reverse=True):
        '''If self.isdir and self.exists, return an iterable of fileobjects
        corresponding to its direct content (non-recursive).
        Otherwise, log an error and return ().
        '''
        try:
            content = _unicode_listdir(self.fullpath)
            if sort:
                content = sorted(content, reverse=reverse)
            return (File(name, parent=self) for name in content)
        except OSError as error:
            log.e(_('cannot list directory: %s'), error)
            return ()


    @classmethod
    def inputfilter(cls, files_iter):
        basedir = cherry.config['media.basedir']
        for f in files_iter:
            if not f.exists:
                log.e(_('file not found: %s. skipping.' % f.fullpath))
                continue
            if not f.fullpath.startswith(basedir):
                log.e(_('file not in basedir: %s. skipping.') % f.fullpath)
                continue
            if f.islink and not os.path.isfile(f.fullpath):
                rp = os.path.realpath(f.fullpath)
                if os.path.abspath(basedir).startswith(rp) \
                    or (os.path.islink(basedir)
                        and
                        os.path.realpath(basedir).startswith(rp)):
                    log.e(_(("Cyclic symlink found: %s creates a circle "
                             "if followed. Skipping.")) % f.relpath)
                    continue
                if not (f.parent is None or f.parent.parent is None):
                    log.e(_(("Deeply nested directory symlink found: %s . "
                          "All symlinks to directories "
                          "must be directly in your basedir (%s). The "
                          "program cannot safely handle them otherwise."
                          " Skipping.")) % (f.relpath, os.path.abspath(basedir)))
                    continue
            yield f

class MemoryDB:
    def __init__(self, db_file, table_to_dump):
        log.i(_("Loading files database into memory..."))
        self.db = sqlite3.connect(':memory:', check_same_thread=False)
        cu = self.db.cursor()
        cu.execute('attach database "%s" as attached_db' % db_file)
        cu.execute("select sql from attached_db.sqlite_master "
                   "where type='table' and name='" + table_to_dump + "'")
        sql_create_table = cu.fetchone()[0]
        cu.execute(sql_create_table);
        cu.execute("insert into " + table_to_dump +
                   " select * from attached_db." + table_to_dump)
        self.db.commit()
        cu.execute("detach database attached_db")


