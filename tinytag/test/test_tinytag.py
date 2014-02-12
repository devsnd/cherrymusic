from __future__ import unicode_literals
from os import path
import nose

from tinytag import *

testfiles = {'vbri.mp3': {'track_total': None, 'length': 0.5224489795918368, 'album': 'I Can Walk On Water I Can Fly', 'year': '2007', 'title': 'I Can Walk On Water I Can Fly', 'artist': 'Basshunter', 'track': '01'},
             'cbr.mp3': {'track_total': None, 'length': 0.4963265306122449, 'album': 'I Can Walk On Water I Can Fly', 'year': '2007', 'title': 'I Can Walk On Water I Can Fly', 'artist': 'Basshunter', 'track': '01'},
             'id3v22-test.mp3': {'track_total': '11', 'length': 0.156734693877551, 'album': 'Hymns for the Exiled', 'year': '2004', 'title': 'cosmic american', 'artist': 'Anais Mitchell', 'track': '3'},
             'silence-44-s-v1.mp3': {'track_total': None, 'length': 3.7355102040816326, 'album': 'Quod Libet Test Data', 'year': '2004', 'title': 'Silence', 'artist': 'piman', 'track': '2'},
             'empty.ogg': {'track_total': None, 'length': 3.684716553287982, 'album': None, '_max_samplenum': 162496, 'year': None, 'title': None, 'artist': None, 'track': None, '_tags_parsed': False},
             'multipagecomment.ogg': {'track_total': None, 'length': 3.684716553287982, 'album': None, '_max_samplenum': 162496, 'year': None, 'title': None, 'artist': None, 'track': None, '_tags_parsed': False},
             'multipage-setup.ogg': {'track_total': None, 'length': 4.128798185941043, 'album': 'Timeless', '_max_samplenum': 182080, 'year': '2006', 'title': 'Burst', 'artist': None, 'track': '7', '_tags_parsed': False},
             'test.ogg': {'track_total': None, 'length': 1.0, 'album': 'the boss', '_max_samplenum': 44100, 'year': '2006', 'title': 'the boss', 'artist': None, 'track': '1', '_tags_parsed': False},
             'test.wav': {'length': 1.0},
             'test3sMono.wav': {'length': 3.0},
             'test-tagged.wav': {'length': 1.0},
             
             'flac1sMono.flac': {'track_total': None, 'album': None, 'year': None, 'length': 1.0, 'title': None, 'track': None, 'artist': None},
             'flac1.5sStereo.flac': {'track_total': None, 'album': None, 'year': None, 'length': 1.4995238095238095, 'title': None, 'track': None, 'artist': None},
             'flac_application.flac': {'track_total': None, 'album': 'Belle and Sebastian Write About Love', 'year': '2010-10-11', 'length': 273.64, 'title': 'I Want the World to Stop', 'track': '4/11', 'artist': 'Belle and Sebastian'},
             'no-tags.flac': {'track_total': None, 'album': None, 'year': None, 'length': 3.684716553287982, 'title': None, 'track': None, 'artist': None},
             'variable-block.flac': {'track_total': None, 'album': 'Appleseed Original Soundtrack', 'year': '2004', 'length': 261.68, 'title': 'DIVE FOR YOU', 'track': '01', 'artist': None},
             }


def get_info(testfile, expected):
    folder = path.join(path.dirname(__file__), 'samples')
    filename = path.join(folder, testfile)
    print(filename)
    tag = TinyTag.get(filename)
    for key, expcvalue in expected.items():
        result = getattr(tag, key)
        fmt_string = 'expected "%s": %s (%s) got %s (%s)!'
        fmt_values = (key, repr(expcvalue), type(expcvalue), repr(result), type(result))
        assert result == expcvalue, fmt_string % fmt_values
    print(tag)
    print('')


def test_generator():
    for testfile, expected in testfiles.items():
        yield get_info, testfile, expected


if __name__ == '__main__':
    nose.runmodule()
