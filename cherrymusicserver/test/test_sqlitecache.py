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

import unittest

import os
import shutil
import sqlite3
import tempfile

import cherrymusicserver as cherry
from cherrymusicserver import configuration
from cherrymusicserver import log
from cherrymusicserver import sqlitecache

log.setTest()

class TestFile(object):

    def __init__(self, fullpath, parent=None, isdir=None):
        self.uid = -1
        self.fullpath = fullpath
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


    @classmethod
    def enumerate_files_in(cls, somewhere, sort):
        raise NotImplementedError("%s.%s.enumerate_files_in(cls, paths, sort)"
                                  % (__name__, cls.__name__))

tmpdir = None
oldwd = os.getcwd()

def setUpModule():
    global tmpdir
    tmpdir = tempfile.mkdtemp(suffix='-test_sqlitecache', prefix='tmp-cherrymusic-')
    os.chdir(tmpdir)

def tearDownModule():
    os.chdir(oldwd)
    shutil.rmtree(tmpdir, ignore_errors=False, onerror=None)

def getAbsPath(relpath):
    'returns the absolute path for a path relative to the global testdir'
    return os.path.join(tmpdir, relpath)


def setupTestfile(testfile):
    if testfile.isdir:
        os.makedirs(testfile.fullpath, exist_ok=True)
    else:
        if not os.path.exists(testfile.fullpath):
            open(testfile.fullpath, 'w').close()


def setupTestfiles(testdir, testfiles):
    os.makedirs(testdir, exist_ok=True)
    os.chdir(testdir)
    for filename in testfiles:
        setupTestfile(TestFile(filename))
    os.chdir('..')


def removeTestfile(testfile):
    if testfile.isdir:
        os.rmdir(testfile.fullpath)
    else:
        os.remove(testfile.fullpath)


def removeTestfiles(testdir, testfiles):
    shutil.rmtree(testdir, ignore_errors=True, onerror=None)



class AddFilesToDatabaseTest(unittest.TestCase):

    testdir = 'empty'

    def setupConfig(self):
        cherry.config = configuration.from_defaults()
        cherry.config.media.basedir = self.testdir


    def setUp(self):
        setupTestfiles(self.testdir, ())
        self.setupConfig()
        self.Cache = sqlitecache.SQLiteCache(':memory:')


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

        res = self.Cache.conn.execute('SELECT * from files WHERE rowid=?', (file.uid,)).fetchall()

        self.assertTrue(1 == len(res), "expect exactly one file with that uid")
        self.assertTrue(4 == len(res[0]), "expect exactly four colums stored per file")

        parentid, fname, fext, isdir = res[0]
        self.assertTrue(parent.uid == parentid, "correct parent id must be saved")
        self.assertTrue('filename' == fname, "filename must be saved without extension")
        self.assertTrue('.extension' == fext, "extension must be saved with leading .")
        self.assertFalse(isdir, 'isdir must not be set in files table')

        isdir = self.Cache.conn.execute('SELECT isdir from files WHERE rowid=?', (parent.uid,)).fetchone()[0]
        self.assertTrue(isdir, "isdir must be saved correctly")


    def test_add_to_dictionary_table(self):
        """searchable parts of a filename must be added to the dictionary as
        words, and a list of unique word ids returned"""

        filename = 'abc ÖÄUßé.wurst_-_blablabla.nochmal.wurst'
        words = sqlitecache.SQLiteCache.searchterms(filename)

        ids = self.Cache.add_to_dictionary_table(filename)

        wordset = set(words)
        self.assertTrue(len(wordset) < len(words), "there must be duplicate words in the test")
        idset = set(ids)
        self.assertTrue(len(ids) == len(idset), "there must be no duplicate ids")
        for word in wordset:
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
        self.assertTrue(expected.fullpath == actual.fullpath, "equal fullpath %s vs %s" % (expected.fullpath, actual.fullpath))
        self.assertTrue(expected.name == actual.name, "equal name %s vs %s " % (expected.name, actual.name))
        self.assertTrue(expected.ext == actual.ext, 'equal extension %s vs %s' % (expected.ext, actual.ext))
        self.assertTrue(expected.isdir == actual.isdir, 'equal dir flag %s vs %s (%s)' % (expected.isdir, actual.isdir, expected.fullpath))


    def testFileClass(self):
        for filename in self.testfiles:
            filename = os.path.join(self.testdir, filename)
            expected = TestFile(filename)
            if filename.endswith(os.path.sep):
                filename = filename[:-1]
            actual = sqlitecache.File(filename)
            self.assertFilesEqual(expected, actual)


    def testFileEnumerator(self):
        basedir = self.testdir
        testfiles = self.testfiles
        rootpaths = [x for x in
                     [
                      (f[:-1] if f.endswith(os.path.sep) else f)
                      for f in testfiles
                      ]
                     if not os.path.sep in x]
        checklist = [basedir + os.path.sep + f for f in
                     [x[:-1]
                      if x.endswith(os.path.sep)
                      else x
                      for x in testfiles]
                     ]

        for fileobj in sqlitecache.File.enumerate_files_in(rootpaths, basedir=basedir, sort=True):
            path = fileobj.fullpath
            self.assertTrue(path in checklist, 'file returned (%s) must be in expected set (%s)' % (path, checklist))
            self.assertTrue(os.path.exists(path), 'file must exists: %s' % (path,))
            checklist.remove(path)
        self.assertTrue(len(checklist) == 0, 'all files were not enumerated. remaining=%s' % checklist)


class RemoveFilesFromDatabaseTest(unittest.TestCase):

    testdir = 'deltest'

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
        cherry.config.media.basedir = self.testdir
        cherry.config.search.autoupdate = 'True'


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
        setupTestfiles(self.testdir, self.testfiles)
        self.setupConfig()
        self.Cache = sqlitecache.SQLiteCache(':memory:')
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

        self.Cache.remove_dead_file_entries(fob.root.fullpath)

        self.assertFalse(self.fileid_in_db(fob.uid),
                    'file entry must be removed from db')


    def testFilesWithSameNameAsMissingAreNotRemoved(self):
        fob = self.fileobjects['root_dir/first_dir/first_file']
        removeTestfile(fob)
        beforecount = self.db_count('files')

        self.Cache.remove_dead_file_entries(fob.root.fullpath)

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

        self.Cache.remove_dead_file_entries(removelist[0].root.fullpath)

        for fob in removelist:
            self.assertFalse(self.fileid_in_db(fob.uid),
                        'all children entries from removed dir must be removed')


    def testRemoveFileAlsoRemovesSearchIndexes(self):
        fob = self.fileobjects['root_file']
        removeTestfile(fob)

        self.Cache.remove_dead_file_entries(fob.root.fullpath)

        searchids = self.Cache.conn.execute('SELECT count(*) FROM search'
                                            ' WHERE frowid=?', (fob.uid,)) \
                                            .fetchone()[0]
        self.assertEqual(0, searchids,
                         'all search indexes referencing removed file must also be removed')


    def testRemoveAllIndexesForWordRemovesWord(self):
        fob = self.fileobjects[os.path.join('commonName', 'commonname_uniquename')]
        removeTestfile(fob)

        self.Cache.remove_dead_file_entries(fob.root.fullpath)

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

        # SETUP
        self.Cache = sqlitecache.SQLiteCache('test.db')

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
        class BoobyTrap(sqlite3.Connection):
            exceptcount = 0

            def execute(self, stmt, parameters=None):
                '''triggers an Exception when the 'undeletable' item should be 
                removed. relies on way too much knowledge of Cache internals. :(
                '''

                if stmt.lower().startswith('delete from files') \
                  and parameters[0] == undeletable.uid:
                    self.__class__.exceptcount += 1
                    raise Exception("boom goes the dynamite")
                return super().execute(stmt, parameters)

        self.Cache.conn.close()
        self.Cache.conn = BoobyTrap('test.db')

        # RUN
        self.Cache.remove_dead_file_entries(removelist[0].root.fullpath)
        removed = [f for f in removelist if not self.fileid_in_db(f.uid)]

        # CLEANUP
        self.Cache.conn.close()
        os.remove('test.db')

        # ASSERT
        self.assertLessEqual(1, BoobyTrap.exceptcount,
                         'test must have raised at least one exception')

        self.assertListEqual(deletable, removed,
                        'complete rollback must restore all deleted entries.')


class SymlinkTest(unittest.TestCase):

    testdir = 'linktest'

    testfiles = (
                 os.path.join('root_file'),
                 os.path.join('root_dir', ''),
                 )


    def setUp(self):
        setupTestfiles(self.testdir, self.testfiles)


    def tearDown(self):
        removeTestfiles(self.testdir, self.testfiles)


    def enumeratedTestdir(self):
        return [os.path.join(self.testdir, f.relpath) for f in sqlitecache.File\
                .enumerate_files_in(os.listdir(self.testdir),
                                    os.path.abspath(self.testdir))
                ]


    def testRootLinkOk(self):
        link = os.path.join(self.testdir, 'link')
        target = os.path.join(self.testdir, 'root_file')
        os.symlink(target, link)

        try:
            self.assertTrue(link in self.enumeratedTestdir(),
                            'root level links must be returned')
        finally:
            os.remove(link)


    def testSkipSymlinksBelowBasedirRoot(self):
        link = os.path.join(self.testdir, 'root_dir', 'link')
        target = os.path.join(self.testdir, 'root_file')
        os.symlink(target, link)

        try:
            self.assertFalse(link in self.enumeratedTestdir(),
                            'deeply nested link must not be returned')
        finally:
            os.remove(link)


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
                 )

    def setupLog(self):
        log.level(log.DEBUG)

    def setupConfig(self):
        cherry.config = configuration.from_defaults()
        cherry.config.media.basedir = self.testdir
        cherry.config.search.autoupdate = 'True'

    def setupCache(self):
        self.Cache = sqlitecache.SQLiteCache(':memory:')

    def clearCache(self):
        self.Cache.conn.execute('delete from files')
        self.Cache.conn.execute('delete from dictionary')
        self.Cache.conn.execute('delete from search')

    def setUp(self):
        self.testdir = getAbsPath(self.testdirname)
        setupTestfiles(self.testdir, self.testfiles)
        self.setupLog()
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
            self.assertTrue(item.indb.relpath in expected_files, '%s %s' % (item.indb.relpath, expected_files))
            expected_files.remove(item.indb.relpath)
        self.assertEqual(0, len(expected_files))


    def test_update(self):
        self.clearCache()
        cherry.config.media.basedir = '/media/audio/+audiobooks'
        self.Cache.full_update()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
