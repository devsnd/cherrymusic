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

import cherrymusic as cherry
from cherrymusic import configuration
from cherrymusic import sqlitecache

class TestFile(object):

    def __init__(self, fullpath, parent=None, isdir=None):
        self.uid = -1
        self.fullpath = fullpath
        self.parent = parent
        self.isdir = fullpath.endswith('/') if (isdir is None) else isdir
        if self.isdir:
            self.fullpath = fullpath[:-1]
            self.name = os.path.basename(self.fullpath)
            self.ext = ''
        else:
            self.name, self.ext = os.path.splitext(os.path.basename(fullpath))


    @classmethod
    def enumerate_files_in(cls, somewhere, sort):
        raise NotImplementedError("%s.%s.enumerate_files_in(cls, paths, sort)" % (__name__, __class__.__name__))


class AddFilesToDatabaseTest(unittest.TestCase):

    testdir = 'testfiles'
    testfiles = (
                 'rootlevelfile',
                 'first/',
                 'first/firstlevelfile',
                 'first/second/',
                 'first/second/secondlevelfile',
                 )


    def setupTestfiles(self):
        os.makedirs('empty', exist_ok=True)


    def removeTestfiles(self):
        os.rmdir('empty')


    def setupConfig(self):
        cherry.config = configuration.from_defaults()
        cherry.config.media.basedir = 'empty'
        cherry.config.search.cachefile = ':memory:'


    def setUp(self):
        self.setupTestfiles()
        self.setupConfig()
        self.Cache = sqlitecache.SQLiteCache()


    def tearDown(self):
        self.removeTestfiles()
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
        print(words)

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
                 'rootlevelfile',
                 'first/',
                 'first/firstlevelfile',
                 'first/second/',
                 'first/second/secondlevelfile',
                 'nonASCIItest/',
                 'nonASCIItest/öäßÖÄÉ',
                 )


    def setupTestfile(self, testfile):
        if testfile.isdir:
            os.makedirs(testfile.fullpath, exist_ok=True)
        else:
            if not os.path.exists(testfile.fullpath):
                open(testfile.fullpath, 'w').close()


    def setupTestfiles(self):
        import sys
        print(sys.version)
        os.makedirs(__class__.testdir, exist_ok=True)
        os.chdir(__class__.testdir)
        for filename in __class__.testfiles:
            self.setupTestfile(TestFile(filename))
        os.chdir('..')


    def removeTestfile(self, testfile):
        if testfile.isdir:
            os.rmdir(testfile.fullpath)
        else:
            os.remove(testfile.fullpath)


    def removeTestfiles(self):
        os.chdir(__class__.testdir)
        for testfile in reversed(__class__.testfiles):
            self.removeTestfile(TestFile(testfile))
        os.chdir('..')
        os.rmdir(__class__.testdir)


    def setUp(self):
        self.setupTestfiles()


    def tearDown(self):
        self.removeTestfiles()


    def assertFilesEqual(self, expected, actual):
        self.failUnless(expected.fullpath == actual.fullpath, "equal fullpath %s vs %s" % (expected.fullpath, actual.fullpath))
        self.failUnless(expected.name == actual.name, "equal name %s vs %s " % (expected.name, actual.name))
        self.failUnless(expected.ext == actual.ext, 'equal extension %s vs %s' % (expected.ext, actual.ext))
        self.failUnless(expected.isdir == actual.isdir, 'equal dir flag %s vs %s (%s)' % (expected.isdir, actual.isdir, expected.fullpath))


    def testFileClass(self):
        for filename in __class__.testfiles:
            filename = __class__.testdir + '/' + filename
            expected = TestFile(filename)
            if filename.endswith('/'):
                filename = filename[:-1]
            actual = sqlitecache.File(filename)
            self.assertFilesEqual(expected, actual)


    def testFileEnumerator(self):
        basedir = __class__.testdir
        testfiles = __class__.testfiles
        rootpaths = [x for x in [(f[:-1] if f.endswith('/') else f) for f in testfiles] if not '/' in x]
        checklist = [basedir + '/' + f for f in [x[:-1] if x.endswith('/') else x for x in testfiles]]

        for path in sqlitecache.File.enumerate_files_in(rootpaths, basedir=basedir, sort=True):
            path = path.fullpath
            self.failUnless(path in checklist, 'file returned (%s) was not in expected set (%s)' % (path, checklist))
            self.failUnless(os.path.exists(path), 'file actually exists: %s' % (path,))
            checklist.remove(path)
        self.failUnless(len(checklist) == 0, 'all files were enumerated? remaining=%s' % checklist)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
