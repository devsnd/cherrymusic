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
from pprint import pprint

import cherrymusic as cherry
from cherrymusic import configuration
from cherrymusic import log
from cherrymusic import sqlitecache
from IPython.core.history import sqlite3

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
    os.chdir(testdir)
    for testfile in reversed(testfiles):
        try:
            removeTestfile(TestFile(testfile))
        except OSError as e:
            if not e.errno == 2:    # ignore missing files and directories
                raise e
    os.chdir('..')
    os.rmdir(testdir)



class AddFilesToDatabaseTest(unittest.TestCase):

    testdir = 'empty'

    def setupConfig(self):
        cherry.config = configuration.from_defaults()
        cherry.config.media.basedir = 'empty'


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

        self.failUnless(file.uid >= 0, "file has valid rowid")

        res = self.Cache.conn.execute('SELECT * from files WHERE rowid=?', (file.uid,)).fetchall()

        self.failUnless(1 == len(res), "exactly one file with that uid")
        self.failUnless(4 == len(res[0]), "expect exactly four colums stored per file")

        parentid, fname, fext, isdir = res[0]
        self.failUnless(parent.uid == parentid, "correct parent id got saved")
        self.failUnless('filename' == fname, "filename got saved without extension")
        self.failUnless('.extension' == fext, "extension got saved with leading .")
        self.failIf(isdir, 'isdir somehow got set in files table')

        isdir = self.Cache.conn.execute('SELECT isdir from files WHERE rowid=?', (parent.uid,)).fetchone()[0]
        self.failUnless(isdir, "isdir got saved correctly")


    def test_add_to_dictionary_table(self):
        filename = 'abc ÖÄUßé.wurst_-_blablabla.nochmal.wurst'
        words = sqlitecache.SQLiteCache.searchterms(filename)

        ids = self.Cache.add_to_dictionary_table(filename)

        wordset = set(words)
        self.failUnless(len(wordset) < len(words), "there were duplicate words in the test")
        idset = set(ids)
        self.failUnless(len(ids) == len(idset), "function returned no duplicate ids")
        for word in wordset:
            cursor = self.Cache.conn.execute('SELECT rowid FROM dictionary WHERE word=?', (word,))
            res = cursor.fetchall()
            self.failUnless(len(res) == 1, "exactly one row per word")
            self.failUnless(len(idset) > 0, "there are unmatched ids")
            self.failUnless(res[0][0] in idset, "word id got returned by function")
            idset.remove(res[0][0])   # make sure no other tested word can use that id to pass
        self.failUnless(len(idset) == 0, "all ids accounted for")


    def test_add_to_search_table(self):
        fileid = 99
        wordids = (13, 42)

        self.Cache.add_to_search_table(fileid, wordids)

        for wid in wordids:
            found = self.Cache.conn.execute('SELECT frowid FROM search WHERE drowid=?', (wid,)).fetchone()[0]
            self.failUnless(fileid == found, 'fileid was associated with wordid')


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
            self.failUnless(filename in found, "all added files are findable by cache search")




class FileTest(unittest.TestCase):

    testdir = 'testfiles'
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
        self.failUnless(expected.fullpath == actual.fullpath, "equal fullpath %s vs %s" % (expected.fullpath, actual.fullpath))
        self.failUnless(expected.name == actual.name, "equal name %s vs %s " % (expected.name, actual.name))
        self.failUnless(expected.ext == actual.ext, 'equal extension %s vs %s' % (expected.ext, actual.ext))
        self.failUnless(expected.isdir == actual.isdir, 'equal dir flag %s vs %s (%s)' % (expected.isdir, actual.isdir, expected.fullpath))


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
            self.failUnless(path in checklist, 'file returned (%s) was not in expected set (%s)' % (path, checklist))
            self.failUnless(os.path.exists(path), 'file actually exists: %s' % (path,))
            checklist.remove(path)
        self.failUnless(len(checklist) == 0, 'all files were enumerated? remaining=%s' % checklist)


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

        self.failIf(self.fileid_in_db(fob.uid),
                    'file entry did not get removed from db')


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
            self.failIf(self.fileid_in_db(fob.uid),
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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
