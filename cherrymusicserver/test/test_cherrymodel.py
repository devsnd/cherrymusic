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

import nose
import os

from mock import *
from nose.tools import *

from cherrymusicserver.test.helpers import cherrytest, tempdir, mkpath, cherryconfig, symlinktest

from cherrymusicserver import log
log.setTest()

from cherrymusicserver import cherrymodel
from cherrymusicserver import sqlitecache

def config(cfg=None):
    c = {'media.basedir': os.path.join(os.path.dirname(__file__), 'data_files')}
    if cfg:
        c.update(cfg)
    return c


@cherrytest(config({'browser.pure_database_lookup': False}))
def test_hidden_names_listdir():
    import cherrymusicserver as cherry
    basedir_listing = sorted(os.listdir(cherry.config['media.basedir']))
    eq_(['.hidden.mp3', 'empty_file.mp3', 'not_hidden.mp3'], basedir_listing)

    model = cherrymodel.CherryModel()
    dir_listing = model.listdir('')
    assert len(dir_listing) == 1, str(dir_listing)
    assert dir_listing[0].path == 'not_hidden.mp3'

@raises(ValueError)
@cherrytest(config({'browser.pure_database_lookup': False}))
def test_listdir_in_filesystem_must_be_inside_basedir():
    model = cherrymodel.CherryModel()
    model.listdir('./../')
# sqlitecache is covered in test_sqlitecache.test_listdir()

@cherrytest(config({'search.maxresults': 10}))
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.cherrypy')
def test_hidden_names_search(cherrypy, cache):
    model = cherrymodel.CherryModel()

    cache.searchfor.return_value = [cherrymodel.MusicEntry('.hidden.mp3', dir=False)]
    assert not model.search('something')

    cache.searchfor.return_value = [cherrymodel.MusicEntry('not_hidden.mp3', dir=False)]
    assert model.search('something')


@cherrytest(config({'browser.pure_database_lookup': True}))
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
def test_listdir_deleted_files(cache):
    "cherrymodel.listdir should work when cached files don't exist anymore"
    model = cherrymodel.CherryModel()

    cache.listdir.return_value = ['deleted.mp3']
    eq_([], model.listdir(''))


@symlinktest
@cherrytest(config({'browser.pure_database_lookup': False}))
def test_listdir_bad_symlinks():
    "cherrymodel.listdir should work when cached files don't exist anymore"
    model = cherrymodel.CherryModel()

    with tempdir('test_listdir_bad_symlinks') as tmpdir:
        with cherryconfig({'media.basedir': tmpdir}):
            os.symlink('not_there', os.path.join(tmpdir, 'badlink'))
            eq_([], model.listdir(''))


@cherrytest(config({'browser.pure_database_lookup': False}))
def test_listdir_unreadable():
    "cherrymodel.listdir should return empty when dir is unreadable"
    model = cherrymodel.CherryModel()

    with tempdir('test_listdir_unreadable') as tmpdir:
        with cherryconfig({'media.basedir': tmpdir}):
            os.chmod(tmpdir, 0o311)
            try:
                open(os.path.join(tmpdir, 'file.mp3'), 'a').close()
                eq_([], model.listdir(''))
            finally:
                # Ensure tmpdir can be cleaned up, even if test fails
                os.chmod(tmpdir, 0o755)


@cherrytest(config({'media.transcode': False}))
def test_randomMusicEntries():
    model = cherrymodel.CherryModel()

    def makeMusicEntries(n):
        return [cherrymodel.MusicEntry(str(i)) for i in range(n)]

    with patch('cherrymusicserver.cherrymodel.CherryModel.cache') as mock_cache:
        with patch('cherrymusicserver.cherrymodel.CherryModel.isplayable') as mock_playable:
            mock_cache.randomFileEntries.side_effect = makeMusicEntries

            mock_playable.return_value = True
            eq_(2, len(model.randomMusicEntries(2)))

            mock_playable.return_value = False
            eq_(0, len(model.randomMusicEntries(2)))


@cherrytest({'media.transcode': False})
def test_isplayable():
    """ existing, nonempty files of supported types should be playable """
    model = cherrymodel.CherryModel()

    with patch(
        'cherrymusicserver.cherrymodel.CherryModel.supportedFormats', ['mp3']):

        with tempdir('test_isplayable') as tmpdir:
            mkfile = lambda name, content='': mkpath(name, tmpdir, content)
            mkdir = lambda name: mkpath(name + '/', tmpdir)

            with cherryconfig({'media.basedir': tmpdir}):
                isplayable = model.isplayable
                assert isplayable(mkfile('ok.mp3', 'content'))
                assert not isplayable(mkfile('empty.mp3'))
                assert not isplayable(mkfile('bla.unsupported', 'content'))
                assert not isplayable(mkdir('directory.mp3'))
                assert not isplayable('inexistant')


@cherrytest({'media.transcode': True})
def test_is_playable_by_transcoding():
    """ filetypes should still be playable if they can be transcoded """
    from audiotranscode import AudioTranscode

    with patch('audiotranscode.AudioTranscode', spec=AudioTranscode) as ATMock:
        ATMock.return_value = ATMock
        ATMock.available_decoder_formats.return_value = ['xxx']
        with tempdir('test_isplayable_by_transcoding') as tmpdir:
            with cherryconfig({'media.basedir': tmpdir}):
                track = mkpath('track.xxx', parent=tmpdir, content='xy')
                model = cherrymodel.CherryModel()
                ok_(model.isplayable(track))


@cherrytest({'media.transcode': False})
@patch('cherrymusicserver.cherrymodel.cherrypy', MagicMock())
def test_search_results_missing_in_filesystem():
    "inexistent MusicEntries returned by sqlitecache search should be ignored"
    cache_finds = [
        cherrymodel.MusicEntry('i-dont-exist.dir', dir=True),
        cherrymodel.MusicEntry('i-dont-exist.mp3', dir=False),
        cherrymodel.MusicEntry('i-exist.dir', dir=True),
        cherrymodel.MusicEntry('i-exist.mp3', dir=False),
    ]
    mock_cache = Mock(spec=sqlitecache.SQLiteCache)
    mock_cache.searchfor.return_value = cache_finds
    model = cherrymodel.CherryModel()
    model.cache = mock_cache

    with tempdir('test_cherrymodel_search_missing_results') as tmpdir:
        mkpath('i-exist.dir/', tmpdir)
        mkpath('i-exist.mp3', tmpdir, 'some content')

        with cherryconfig({'media.basedir': tmpdir}):
            results = model.search('the query')
            eq_(set(cache_finds[2:]), set(results))


if __name__ == '__main__':
    nose.runmodule()
