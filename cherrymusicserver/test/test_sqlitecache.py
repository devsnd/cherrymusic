#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
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

import nose
import unittest
from nose.tools import *

from cherrymusicserver.test.helpers import cherrytest, tempdir, symlinktest

import os
import re
import shutil
import sys
import tempfile

import cherrymusicserver as cherry
from cherrymusicserver import configuration
from cherrymusicserver import database
from cherrymusicserver import log
from cherrymusicserver import sqlitecache
from cherrymusicserver import service

sqlitecache.debug = True

from cherrymusicserver.database.sql import MemConnector
log.setTest()


class TestFile(object):

    def __init__(self, fullpath, parent=None, isdir=None, uid=None):
        self.uid = uid if uid else -1
        self.fullpath = fullpath if not parent else os.path.join(parent.fullpath, fullpath)
        self.parent = parent
        self.isdir = fullpath.endswith(os.path.sep) if (isdir is None) else isdir
        if self.isdir:
            self.fullpath = fullpath[:-1]
            self.name = os.path.basename(self.fullpath)
            self.ext = ''
        else:
            self.name, self.ext = os.path.splitext(os.path.basename(fullpath))

    def __repr__(self):
        return '[%d] %s%s (-> %d)' % (self.uid,
                                  self.name + self.ext,
                                  '*' if self.isdir else '',
                                  - 1 if self.parent is None
                                    else self.parent.uid)

    @property
    def exists(self):
        return os.path.exists(self.fullpath)


    @classmethod
    def enumerate_files_in(cls, somewhere, sort):
        raise NotImplementedError("%s.%s.enumerate_files_in(cls, paths, sort)"
                                  % (__name__, cls.__name__))

tmpdir = None
def setUpModule():
    global tmpdir
    tmpdir = tempfile.mkdtemp(suffix='-test_sqlitecache', prefix='tmp-cherrymusic-')
if sys.version_info < (2, 7):  # hack to support python 2.6 which doesn't setUpModule()
    setUpModule()

def tearDownModule():
    shutil.rmtree(tmpdir, ignore_errors=False, onerror=None)

def getAbsPath(*relpath):
    'returns the absolute path for a path relative to the global testdir'
    return os.path.join(tmpdir, *relpath)


def setupTestfile(testfile):
    if testfile.isdir:
        setupDir(testfile.fullpath)
        # os.makedirs(testfile.fullpath, exist_ok=True)
    else:
        if not os.path.exists(testfile.fullpath):
            open(testfile.fullpath, 'w').close()
    assert testfile.exists


def setupTestfiles(testdir, testfiles):
    testdir = os.path.join(tmpdir, testdir, '')
    setupTestfile(TestFile(testdir))
    for filename in testfiles:
        filename = os.path.join(testdir, filename)
        setupTestfile(TestFile(filename))


def setupDir(testdir):
    import errno
    try:
        os.makedirs(testdir)  #, exist_ok=True) # py2 compatibility
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(testdir):
            pass
        else:
            raise

def removeTestfile(testfile):
    if testfile.isdir:
        os.rmdir(testfile.fullpath)
    else:
        os.remove(testfile.fullpath)


def removeTestfiles(testdir, testfiles):
    testdir = os.path.join(tmpdir, testdir)
    shutil.rmtree(testdir, ignore_errors=True, onerror=None)


class AddFilesToDatabaseTest(unittest.TestCase):

    testdirname = 'empty'

    def setupConfig(self):
        cherry.config = configuration.from_defaults()
        cherry.config = cherry.config.replace({'media.basedir': self.testdir})


    def setUp(self):
        self.testdir = getAbsPath(self.testdirname)
        setupTestfiles(self.testdir, ())
        self.setupConfig()
        service.provide('dbconnector', MemConnector)
        database.ensure_current_version(sqlitecache.DBNAME, autoconsent=True)
        self.Cache = sqlitecache.SQLiteCache()
        self.Cache.full_update()


    def tearDown(self):
        removeTestfiles(self.testdir, ())
        self.Cache.conn.close()


    def test_add_to_file_table(self):
        parent = TestFile('test/', parent=None, isdir=True)
        parent.uid = 42
        file = TestFile('test/filename.extension', parent=parent, isdir=False)

        # RUN
        self.Cache.add_to_file_table(parent)
        self.Cache.add_to_file_table(file)

        self.assertTrue(file.uid >= 0, "file must have valid rowid")

        colnames = ('parent', 'filename', 'filetype', 'isdir')
        res = self.Cache.conn.execute('SELECT %s from files WHERE rowid=?'%(', '.join(colnames),), (file.uid,)).fetchall()

        self.assertTrue(1 == len(res), "expect exactly one file with that uid")
        self.assertTrue(len(colnames) == len(res[0]), "expect exactly %s colums stored per file, got %s" % (len(colnames),len(res[0])))

        resdict = {}
        i=0
        for k in colnames:
            resdict[k] = res[0][i]
            i+=1
        self.assertTrue(parent.uid == resdict['parent'], "correct parent id must be saved")
        self.assertTrue('filename' == resdict['filename'], "filename must be saved without extension")
        self.assertTrue('.extension' == resdict['filetype'], "extension must be saved with leading .")
        self.assertFalse(resdict['isdir'], 'isdir must not be set in files table')

        isdir = self.Cache.conn.execute('SELECT isdir from files WHERE rowid=?', (parent.uid,)).fetchone()[0]
        self.assertTrue(isdir, "isdir must be saved correctly")


    def test_add_to_dictionary_table(self):
        """searchable parts of a filename must be added to the dictionary as
        words, and a list of unique word ids returned"""

        filename = 'abc ÖÄUßé.wurst_-_blablabla.nochmal.wurst'
        words = sqlitecache.SQLiteCache.searchterms(filename)

        ids = self.Cache.add_to_dictionary_table(filename)

        idset = set(ids)
        self.assertTrue(len(ids) == len(idset), "there must be no duplicate ids")
        for word in words:
            cursor = self.Cache.conn.execute('SELECT rowid FROM dictionary WHERE word=?', (word,))
            res = cursor.fetchall()
            self.assertTrue(len(res) == 1, "there must be exactly one matching row per word")
            self.assertTrue(res[0][0] in idset, "the wordid must be returned by the function")
            idset.remove(res[0][0])   # make sure no other tested word can use that id to pass
        self.assertTrue(len(idset) == 0, "there must not be more ids than unique words")


    def test_add_to_search_table(self):
        fileid = 99
        wordids = (13, 42)

        self.Cache.add_to_search_table(fileid, wordids)

        for wid in wordids:
            found = self.Cache.conn.execute('SELECT frowid FROM search WHERE drowid=?', (wid,)).fetchone()[0]
            self.assertTrue(fileid == found, 'fileid must be associated with wordid')


    def test_register_file_with_db(self):
        testnames = (
                     'SUCHMICH',
                     'findmich suchmich',
                     'suchMICH blablub',
                     'wurst-mit-Suchmich.doch-schinken',
                     )

        for filename in testnames:
            self.Cache.register_file_with_db(TestFile(filename))

        found = self.Cache.searchfor('SUCHMICH', 100)
        #map musicentries to string
        found = list(map(lambda x : x.path, found))
        for filename in testnames:
            self.assertTrue(filename in found, "all added files must be findable by cache search")




class FileTest(unittest.TestCase):

    testdir = 'filetest'

    testfiles = (
                 os.path.join('rootlevelfile'),
                 os.path.join('firstdir', ''),
                 os.path.join('firstdir', 'firstlevelfile'),
                 os.path.join('firstdir', 'seconddir', ''),
                 os.path.join('firstdir', 'seconddir', 'secondlevelfile'),
                 os.path.join('nonASCIItest', ''),
                 os.path.join('nonASCIItest', 'öäßÖÄÉ'),
                 )


    def setUp(self):
        setupTestfiles(self.testdir, self.testfiles)


    def tearDown(self):
        removeTestfiles(self.testdir, self.testfiles)

    def assertFilesEqual(self, expected, actual):
        self.assertTrue(actual.exists)
        self.assertTrue(expected.fullpath == actual.fullpath, "equal fullpath %s vs %s" % (expected.fullpath, actual.fullpath))
        self.assertTrue(expected.name == actual.name, "equal name %s vs %s " % (expected.name, actual.name))
        self.assertTrue(expected.ext == actual.ext, 'equal extension %s vs %s' % (expected.ext, actual.ext))
        self.assertTrue(expected.isdir == actual.isdir, 'equal dir flag %s vs %s (%s)' % (expected.isdir, actual.isdir, expected.fullpath))


    def testFileClass(self):
        for filename in self.testfiles:
            filename = os.path.join(tmpdir, self.testdir, filename)
            expected = TestFile(filename)
            if filename.endswith(os.path.sep):
                filename = filename[:-1]
            actual = sqlitecache.File(filename)
            self.assertFilesEqual(expected, actual)


class RemoveFilesFromDatabaseTest(unittest.TestCase):

    testdirname = 'deltest'

    testfiles = (
                 os.path.join('root_file'),
                 os.path.join('root_dir', ''),
                 os.path.join('root_dir', 'first_file'),
                 os.path.join('root_dir', 'first_dir', ''),
                 os.path.join('root_dir', 'first_dir', 'first_file'),
                 os.path.join('commonName', ''),
                 os.path.join('commonName', 'commonname_uniquename'),
                 )

    fileobjects = {}


    def setupConfig(self):
        cherry.config = configuration.from_defaults()
        cherry.config = cherry.config.replace({
            'media.basedir': self.testdir,
        })


    def setupFileObjects(self):
        testpath = os.path.abspath(self.testdir)
        root = sqlitecache.File(testpath)
        self.fileobjects[''] = root
        for path in self.testfiles:
            self.addPathToFileObjects(path, root)


    def addPathToFileObjects(self, path, root):
        path = path.rstrip(os.path.sep)
        ref, base = os.path.split(path)
        if ref:
            if not ref in self.fileobjects:
                self.addPathToFileObjects(ref, root)
            parent = self.fileobjects[ref]
        else:
            parent = root
        fob = sqlitecache.File(base, parent=parent)
        self.id_fileobj(fob)
        self.fileobjects[path] = fob


    def setUp(self):
        self.testdir = getAbsPath(self.testdirname)
        setupTestfiles(self.testdir, self.testfiles)
        self.setupConfig()
        service.provide('dbconnector', MemConnector)
        database.ensure_current_version(sqlitecache.DBNAME, autoconsent=True)
        self.Cache = sqlitecache.SQLiteCache()
        self.Cache.full_update()
        self.setupFileObjects()
        assert self.fileobjects[''].fullpath == os.path.abspath(self.testdir), \
                'precondition: test rootdir has correct fullpath'

    def tearDown(self):
        removeTestfiles(self.testdir, self.testfiles)
        self.Cache.conn.close()


    def lookup_filename(self, filename, parentid):
        return self.Cache.conn.execute(
                        'SELECT rowid FROM files WHERE parent=? AND filename=?',
                        (parentid, filename,))\
                        .fetchone()

    def fileid_in_db(self, fileid):
        return self.Cache.conn.execute('SELECT COUNT(*) FROM files'\
                                       ' WHERE rowid=?', (fileid,))\
                                       .fetchone()[0]


    def id_fileobj(self, fileobj):
        '''fetches the db id for fileobj and saves it in fileobj.uid'''
        if fileobj.parent is None:
            pid = -1
        else:
            if fileobj.parent.uid == -1:
                self.id_fileobj(fileobj.parent)
            pid = fileobj.parent.uid
        res = self.lookup_filename(fileobj.basename, pid)
        if res is None:
            if fileobj != fileobj.root:     # testdir itself is not in db
                log.w('fileobj not in database: %s', fileobj)
            return
        uid = res[0]
        fileobj.uid = uid


    def db_count(self, tablename):
        query = 'SELECT COUNT(*) FROM ' + tablename
        return self.Cache.conn.execute(query).fetchone()[0]


    def testMissingFileIsRemovedFromDb(self):
        fob = self.fileobjects['root_file']
        removeTestfile(fob)
        assert not fob.exists
        assert self.fileid_in_db(fob.uid)

        self.Cache.full_update()

        self.assertFalse(self.fileid_in_db(fob.uid),
                    'file entry must be removed from db')


    def testFilesWithSameNameAsMissingAreNotRemoved(self):
        fob = self.fileobjects['root_dir/first_dir/first_file']
        removeTestfile(fob)
        beforecount = self.db_count('files')

        self.Cache.full_update()

        self.assertEqual(beforecount - 1, self.db_count('files'),
                         'exactly one file entry must be removed')


    def get_fileobjects_for(self, dirname):
        return [self.fileobjects[key] for key
                in sorted(self.fileobjects.keys())
                if key.startswith(dirname)]


    def testMissingDirIsRemovedRecursively(self):
        removelist = self.get_fileobjects_for('root_dir')
        for fob in reversed(removelist):
            removeTestfile(fob)

        self.Cache.full_update()

        for fob in removelist:
            self.assertFalse(self.fileid_in_db(fob.uid),
                        'all children entries from removed dir must be removed')


    def testRemoveFileAlsoRemovesSearchIndexes(self):
        fob = self.fileobjects['root_file']
        removeTestfile(fob)

        self.Cache.full_update()

        searchids = self.Cache.conn.execute('SELECT count(*) FROM search'
                                            ' WHERE frowid=?', (fob.uid,)) \
                                            .fetchone()[0]
        self.assertEqual(0, searchids,
                         'all search indexes referencing removed file must also be removed')


    def testRemoveAllIndexesForWordRemovesWord(self):
        fob = self.fileobjects[os.path.join('commonName', 'commonname_uniquename')]
        removeTestfile(fob)

        self.Cache.full_update()

        unique = self.Cache.conn.execute('SELECT COUNT(*) FROM dictionary'
                                         ' WHERE word=?', ('uniquename',)) \
                                         .fetchone()[0]
        common = self.Cache.conn.execute('SELECT COUNT(*) FROM dictionary'
                                         ' WHERE word=?', ('commonname',)) \
                                         .fetchone()[0]

        self.assertEqual(0, unique,
                         'orphaned words must be removed')
        self.assertEqual(1, common,
                         'words still referenced elsewhere must not be removed')

    def testRollbackOnException(self):

        class BoobytrappedConnector(MemConnector):
            exceptcount = 0

            def __init__(self):
                super(self.__class__, self).__init__()
                self.Connection = type(
                    str('%s.BoobytrappedConnection' % (self.__class__.__module__)),
                    (self.Connection,),
                    {'execute': self.__execute})

            def __execute(connector, stmt, *parameters):
                '''triggers an Exception when the 'undeletable' item should be
                removed. relies on way too much knowledge of Cache internals. :(
                '''
                if stmt.lower().startswith('delete from files') \
                  and parameters[0][0] == undeletable.uid:
                    connector.exceptcount += 1
                    raise Exception("boom goes the dynamite")
                return super(
                    connector.Connection,
                    connector.connection(sqlitecache.DBNAME)).execute(stmt, *parameters)

        # SPECIAL SETUP
        connector = BoobytrappedConnector()
        service.provide('dbconnector', connector)
        database.ensure_current_version(sqlitecache.DBNAME, autoconsent=True)
        self.Cache = sqlitecache.SQLiteCache()
        self.Cache.full_update()

        removelist = self.get_fileobjects_for('root_dir')
        for fob in removelist:
            self.id_fileobj(fob)
        for fob in reversed(removelist):
            removeTestfile(fob)

        undeletable = self.fileobjects[os.path.join('root_dir',
                                                    'first_dir',
                                                    'first_file')]
        deletable = [self.fileobjects[os.path.join('root_dir',
                                                   'first_file')]]



        # RUN
        self.Cache.full_update()
        removed = [f for f in removelist if not self.fileid_in_db(f.uid)]


        # ASSERT
        self.assertTrue(1 <= connector.exceptcount,
                         'test must have raised at least one exception')

        self.assertEqual(deletable, removed,
        # self.assertListEqual(deletable, removed,
                        'complete rollback must restore all deleted entries.')


class RandomEntriesTest(unittest.TestCase):

    testdirname = 'randomFileEntries'

    def setUp(self):
        self.testdir = getAbsPath(self.testdirname)
        setupTestfiles(self.testdir, ())
        cherry.config = cherry.config.replace({'media.basedir': self.testdir})
        service.provide('dbconnector', MemConnector)
        database.ensure_current_version(sqlitecache.DBNAME, autoconsent=True)
        self.Cache = sqlitecache.SQLiteCache()
        return self

    def register_files(self, *paths):
        ''' paths = ('dir/file', 'dir/subdir/') will register
                - directories:
                    - dir/
                    - dir/subdir/
                - files:
                    - /dir/file '''
        files = {}
        for path in paths:
            previous = ''
            for element in re.findall('\w+/?', path):
                fullpath = previous + element
                if fullpath not in files:
                    parent = files.get(previous, None)
                    fileobj = TestFile(element, parent=parent, isdir=element.endswith('/'))
                    self.Cache.register_file_with_db(fileobj)
                    files[fullpath] = fileobj
                previous = fullpath
        return files

    def test_should_return_empty_sequence_when_no_files(self):
        entries = self.Cache.randomFileEntries(10)

        eq_(0, len(entries), entries)

    def test_should_return_empty_sequence_when_zero_count(self):
        entries = self.Cache.randomFileEntries(0)

        eq_(0, len(entries), entries)

    def test_should_return_all_entries_when_fewer_than_count(self):
        self.register_files('a', 'b')

        entries = self.Cache.randomFileEntries(10)

        eq_(2, len(entries), entries)

    def test_should_not_return_deleted_entries(self):
        files = self.register_files('a', 'b', 'c')
        self.Cache.remove_file(files['b'])

        entries = self.Cache.randomFileEntries(10)

        eq_(2, len(entries), entries)

    def test_should_not_return_more_than_count_entries(self):
        self.register_files('a', 'b', 'c')

        entries = self.Cache.randomFileEntries(2)

        ok_(2 >= len(entries), entries)

    def test_should_not_return_dir_entries(self):
        self.register_files('a_dir/a_subdir/')

        entries = self.Cache.randomFileEntries(10)

        eq_(0, len(entries), entries)

    def test_can_handle_entries_in_subdirs(self):
        self.register_files('dir/subdir/file')

        entries = self.Cache.randomFileEntries(10)

        eq_(1, len(entries), entries)
        eq_('dir/subdir/file', entries[0].path, entries[0])


class SymlinkTest(unittest.TestCase):

    testdirname = 'linktest'

    testfiles = (
                 os.path.join('root_file'),
                 os.path.join('root_dir', ''),
                 )


    def setUp(self):
        self.testdir = getAbsPath(self.testdirname)
        setupTestfiles(self.testdir, self.testfiles)
        cherry.config = cherry.config.replace({'media.basedir': self.testdir})
        service.provide('dbconnector', MemConnector)
        database.ensure_current_version(sqlitecache.DBNAME, autoconsent=True)
        self.Cache = sqlitecache.SQLiteCache()

    def tearDown(self):
        removeTestfiles(self.testdir, self.testfiles)
        self.Cache.conn.close()


    def enumeratedTestdir(self):
        return [os.path.join(self.testdir, i.infs.relpath) for
                i in self.Cache.enumerate_fs_with_db(self.testdir)]

    @symlinktest
    def testRootLinkOk(self):
        link = os.path.join(self.testdir, 'link')
        target = os.path.join(self.testdir, 'root_file')
        os.symlink(target, link)

        try:
            self.assertTrue(link in self.enumeratedTestdir(),
                            'root level links must be returned')
        finally:
            os.remove(link)


    @symlinktest
    def testSkipDirSymlinksBelowBasedirRoot(self):
        with tempdir('') as tmpd:
            link = os.path.join(self.testdir, 'root_dir', 'link')
            target = tmpd
            os.symlink(target, link)

            try:
                self.assertFalse(link in self.enumeratedTestdir(),
                                'deeply nested dir link must not be returned')
            finally:
                os.remove(link)


    @symlinktest
    def testNoCyclicalSymlinks(self):
        target = os.path.abspath(self.testdir)
        link = os.path.join(self.testdir, 'link')
        os.symlink(target, link)

        try:
            self.assertFalse(link in self.enumeratedTestdir(),
                            'cyclic link must not be returned')
        finally:
            os.remove(link)


class UpdateTest(unittest.TestCase):

    testdirname = 'updatetest'

    testfiles = (
                 os.path.join('root_file'),
                 os.path.join('root_dir', ''),
                 os.path.join('root_dir', 'first_file'),
                 )


    def setupConfig(self):
        cherry.config = configuration.from_defaults()
        cherry.config = cherry.config.replace({
            'media.basedir': self.testdir,
        })

    def setupCache(self):
        service.provide('dbconnector', MemConnector)
        database.ensure_current_version(sqlitecache.DBNAME, autoconsent=True)
        self.Cache = sqlitecache.SQLiteCache()
        self.Cache.full_update()

    def clearCache(self):
        self.Cache.conn.execute('delete from files')
        self.Cache.conn.execute('delete from dictionary')
        self.Cache.conn.execute('delete from search')

    def setUp(self):
        self.testdir = getAbsPath(self.testdirname)
        setupTestfiles(self.testdir, self.testfiles)
        self.setupConfig()
        self.setupCache()

    def tearDown(self):
        removeTestfiles(self.testdir, self.testfiles)
        self.Cache.conn.close()


    def test_enumerate_add(self):
        '''items not in db must be enumerated'''
        self.clearCache()
        lister = self.Cache.enumerate_fs_with_db(self.testdir)
        expected_files = [f.rstrip(os.path.sep) for f in self.testfiles]
        lister.send(None)  # skip first item
        for item in lister:
            self.assertEqual(None, item.indb, 'database part must be empty, found: %s' % item.indb)
            self.assertTrue(item.infs.relpath in expected_files, '%s %s' % (item.infs.relpath, expected_files))
            expected_files.remove(item.infs.relpath)
        self.assertEqual(0, len(expected_files))


    def test_enumerate_delete(self):
        '''items not in fs must be enumerated'''
        removeTestfiles(self.testdir, self.testfiles)
        lister = self.Cache.enumerate_fs_with_db(self.testdir)
        expected_files = [f.rstrip(os.path.sep) for f in self.testfiles]
        lister.send(None)  # skip first item
        for item in lister:
            self.assertEqual(None, item.infs, 'filesystem part must be empty, found: %s' % item.indb)
            self.assertTrue(item.indb.relpath in expected_files, '%s %s' % (item.indb.relpath, expected_files))
            expected_files.remove(item.indb.relpath)
        self.assertEqual(0, len(expected_files))


    def test_enumerate_same(self):
        '''unchanged fs must have equal db'''
        lister = self.Cache.enumerate_fs_with_db(self.testdir)
        expected_files = [f.rstrip(os.path.sep) for f in self.testfiles]
        lister.send(None)  # skip first item
        for item in lister:
            self.assertEqual(item.infs.fullpath, item.indb.fullpath)
            self.assertEqual(item.infs.isdir, item.indb.isdir)
            self.assertTrue(item.indb.relpath in expected_files, '%s %s' % (item.indb.relpath, expected_files))
            expected_files.remove(item.indb.relpath)
        self.assertEqual(0, len(expected_files))

    def test_new_file_in_known_dir(self):
        newfile = os.path.join('root_dir', 'second_file')
        setupTestfiles(self.testdir, (newfile,))

        self.Cache.full_update()

        self.assertNotEqual(None, self.Cache.db_find_file_by_path(getAbsPath(self.testdir, newfile)),
                            'file must have been added correctly to the database')

    def test_partial_update(self):

        newfiles = (
                      os.path.join('root_dir', 'sub_dir', ''),
                      os.path.join('root_dir', 'sub_dir', 'a_file'),
                      os.path.join('root_dir', 'sub_dir', 'another_file'),
                      )
        setupTestfiles(self.testdir, newfiles)
        path_to = lambda x: getAbsPath(self.testdir, x)

        msg = 'after updating newpath, all paths in newpath must be in database'
        self.Cache.partial_update(path_to(newfiles[0]))
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[0])), msg)
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[1])), msg)
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[2])), msg)

        msg = 'after updating samepath, all paths in samepath must be in database'
        self.Cache.partial_update(path_to(newfiles[0]))
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[0])), msg)
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[1])), msg)
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[2])), msg)

        removeTestfiles(self.testdir, newfiles)

        msg = 'after updating removedpath, all paths in reomevpath must be gone from database'
        self.Cache.partial_update(path_to(newfiles[0]))
        self.assertEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[0])), msg)
        self.assertEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[1])), msg)
        self.assertEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[2])), msg)

        setupTestfiles(self.testdir, newfiles)

        msg = 'after updating newpath/subpath, only newpath and subpath must be in database, not othersubpath'
        self.Cache.partial_update(path_to(newfiles[1]))
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[0])), msg)
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[1])), msg)
        self.assertEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[2])), msg)

        removeTestfiles(self.testdir, newfiles)

        msg = 'after updating removedpath/subpath, subpath most be gone from database, removedpath must still be there'
        self.Cache.partial_update(path_to(newfiles[1]))
        self.assertNotEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[0])), msg)
        self.assertEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[1])), msg)
        self.assertEqual(None, self.Cache.db_find_file_by_path(path_to(newfiles[2])), msg)

def setup_cache(testfiles=()):
    """ Sets up a SQLiteCache instance bound to current `media.basedir`.

        The basedir is assumed to exist (as it must) and can be initialized
        with directories and (empty) files.

        :param list testfiles: Strings of filenames. Names ending in '/' are directories.
    """
    database.resetdb(sqlitecache.DBNAME)
    database.ensure_current_version(sqlitecache.DBNAME, autoconsent=True)
    cache = sqlitecache.SQLiteCache()

    basedir = cherry.config['media.basedir']
    assert not os.listdir(basedir)

    for filename in testfiles:
        fullpath = os.path.join(basedir, filename)
        setupTestfile(TestFile(fullpath))

    cache.full_update()
    return cache


def cachetest(func):
    """ Function decorator that provides a basic CherryMusic context, complete
        with a temporary `media.basedir`.
    """
    testname = '{0}.{1}'.format(func.__module__ , func.__name__)
    def wrapper(*args, **kwargs):
        with tempdir(testname) as basedir:
            testfunc = cherrytest({'media.basedir': basedir})(func)
            testfunc(*args, **kwargs)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


@cachetest
def test_listdir():
    basedir_contents = ['some_file']
    cache = setup_cache(basedir_contents)

    assert basedir_contents == cache.listdir('')
    assert basedir_contents == cache.listdir('.')
    assert basedir_contents == cache.listdir('./.')

    assert [] == cache.listdir('/.')
    assert [] == cache.listdir('..')
    assert [] == cache.listdir('./..')


@cachetest
def test_search_nonascii():
    """ searchfor can handle and find non-ascii """
    basedir_contents = ['ä.mp3']
    cache = setup_cache(basedir_contents)

    found = cache.searchfor('ä')
    assert len(found) == 1
    assert found[0].path == basedir_contents[0]   # found MusicEntry

@symlinktest
@cachetest
def test_symlinks_to_files_are_indexed():
    """ deep file symlinks are indexed """

    # create 'file', 'dir/link' --> 'file'
    cache = setup_cache(['file', 'dir/'])
    basedir = cherry.config['media.basedir']
    src = os.path.join(basedir, 'file')
    dst = os.path.join(basedir, 'dir', 'link')
    os.symlink(src, dst)
    assert os.path.isfile(dst)

    cache.full_update()
    assert cache.searchfor('link')


if __name__ == "__main__":
    nose.runmodule()
