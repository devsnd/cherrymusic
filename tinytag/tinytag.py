#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# tinytag - an audio meta info reader
# Copyright (c) 2014-2015 Tom Wallroth
#
# Sources on github:
# http://github.com/devsnd/tinytag/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>
#

from collections import MutableMapping
import codecs
from functools import reduce
import struct
import os
import io
from io import BytesIO

DEBUG = False  # some of the parsers will print some debug info when set to True

class TinyTagException(Exception):
    pass

def _read(fh, nbytes):  # helper function to check if we haven't reached EOF
    b = fh.read(nbytes)
    if len(b) < nbytes:
        raise TinyTagException('Unexpected end of file')
    return b

class TinyTag(object):
    """Base class for all tag types"""
    def __init__(self, filehandler, filesize):
        self._filehandler = filehandler
        self.filesize = filesize
        self.album = None
        self.albumartist = None
        self.artist = None
        self.audio_offset = 0
        self.bitrate = 0.0  # must be float for later VBR calculations
        self.channels = None
        self.disc = None
        self.disc_total = None
        self.duration = 0
        self.genre = None
        self.samplerate = None
        self.title = None
        self.track = None
        self.track_total = None
        self.year = None
        self._load_image = False
        self._image_data = None

    def get_image(self):
        return self._image_data

    def has_all_tags(self):
        """check if all tags are already defined. Useful for ID3 tags
        since multiple kinds of tags can be in one audio file
        """
        return all((self.track, self.track_total, self.title,
                    self.artist, self.album, self.albumartist,
                    self.year, self.genre))

    @classmethod
    def get(cls, filename, tags=True, duration=True, image=False):
        parser_class = None
        size = os.path.getsize(filename)
        if not size > 0:
            return TinyTag(None, 0)
        if cls == TinyTag:
            """choose which tag reader should be used by file extension"""
            mapping = {
                ('.mp3',): ID3,
                ('.oga', '.ogg', '.opus'): Ogg,
                ('.wav'): Wave,
                ('.flac'): Flac,
                ('.wma'): Wma,
                ('.m4a', '.mp4'): MP4,
            }
            for fileextension, tagclass in mapping.items():
                if filename.lower().endswith(fileextension):
                    parser_class = tagclass
        else:
            # use class on which the method was invoked as parser
            parser_class = cls
        if parser_class is None:
            raise LookupError('No tag reader found to support filetype! ')
        with io.open(filename, 'rb') as af:
            tag = parser_class(af, size)
            tag.load(tags=tags, duration=duration, image=image)
            return tag

    def __str__(self):
        public_attrs = ((k, v) for k, v in self.__dict__.items() if not k.startswith('_'))
        return str(dict(public_attrs))

    def __repr__(self):
        return str(self)

    def load(self, tags, duration, image=False):
        """default behavior of all tags. This method is called in the
        constructors of all tag readers
        """
        if image:
            self._load_image = True
        if tags:
            self._parse_tag(self._filehandler)
        if duration:
            if tags:  # rewind file if the tags were already parsed
                self._filehandler.seek(0)
            self._determine_duration(self._filehandler)

    def _set_field(self, fieldname, bytestring, transfunc=None, overwrite=True):
        """convienience function to set fields of the tinytag by name.
        the payload (bytestring) can be changed using the transfunc"""
        if getattr(self, fieldname):
            return
        value = bytestring if transfunc is None else transfunc(bytestring)
        if fieldname == 'genre' and value.isdigit() and int(value) < len(ID3.ID3V1_GENRES):
            # funky: id3v1 genre hidden in a id3v2 field
            value = ID3.ID3V1_GENRES[int(value)]
        if fieldname in ("track", "disc"):
            current = total = None
            if type(value).__name__ in ('str', 'unicode') and '/' in value:
                current, total = value.split('/')[:2]
                setattr(self, "%s_total" % fieldname, total)
            else:
                current = value
            setattr(self, fieldname, current)
        else:
            setattr(self, fieldname, value)

    def _determine_duration(self, fh):
        raise NotImplementedError()

    def _parse_tag(self, fh):
        raise NotImplementedError()

    def update(self, other):
        """update the values of this tag with the values from another tag"""
        for key in ['track', 'track_total', 'title', 'artist',
                    'album', 'albumartist', 'year', 'duration',
                    'genre', 'disc', 'disc_total']:
            if not getattr(self, key) and getattr(other, key):
                setattr(self, key, getattr(other, key))

    def _bytes_to_int(self, b):
        return reduce(lambda accu, elem: (accu << 8) + elem, b, 0)

    def _bytes_to_int_le(self, b):
        fmt = {1: '<B', 2: '<H', 4: '<I', 8: '<Q'}
        if len(b) not in fmt:
            return 0
        return struct.unpack(fmt[len(b)], b)[0] if len(b) else 0

    def _unpad(self, s):
        # strings in mp3 and asf _can_ be terminated with a zero byte at the end
        return s[:s.index('\x00')] if '\x00' in s else s


class MP4(TinyTag):
    # see: https://developer.apple.com/library/mac/documentation/QuickTime/QTFF/Metadata/Metadata.html
    # and: https://developer.apple.com/library/mac/documentation/QuickTime/QTFF/QTFFChap2/qtff2.html

    class Parser:
        ATOM_DECODER_BY_TYPE = {
            0: lambda x: x, # 'reserved',
            1: lambda x: codecs.decode(x, 'utf-8'),  # UTF-8
            2: lambda x: codecs.decode(x, 'utf-16'), # UTF-16
            3: lambda x: codecs.decode(x, 's/jis'),  # S/JIS
            # 16: duration in millis
            13: lambda x: x, # JPEG
            14: lambda x: x, # PNG
            21: lambda x: struct.unpack('>b', x)[0], # BE Signed Integer
            22: lambda x: struct.unpack('>B', x)[0], # BE Unsigned Integer
            23: lambda x: struct.unpack('>f', x)[0], # BE Float32
            24: lambda x: struct.unpack('>d', x)[0], # BE Float64
            # 27: lambda x: x, # BMP
            # 28: lambda x: x, # QuickTime Metadata atom
            65: lambda x: struct.unpack('b', x)[0],  # 8-bit Signed Integer
            66: lambda x: struct.unpack('>h', x)[0], # BE 16-bit Signed Integer
            67: lambda x: struct.unpack('>i', x)[0], # BE 32-bit Signed Integer
            74: lambda x: struct.unpack('>q', x)[0], # BE 64-bit Signed Integer
            75: lambda x: struct.unpack('B', x)[0],  # 8-bit Unsigned Integer
            76: lambda x: struct.unpack('>H', x)[0], # BE 16-bit Unsigned Integer
            77: lambda x: struct.unpack('>I', x)[0], # BE 32-bit Unsigned Integer
            78: lambda x: struct.unpack('>Q', x)[0], # BE 64-bit Unsigned Integer
        }

        @classmethod
        def make_data_atom_parser(cls, fieldname):
            def parse_data_atom(data_atom):
                data_type = struct.unpack('>I', data_atom[:4])[0]
                conversion = cls.ATOM_DECODER_BY_TYPE.get(data_type)
                if conversion is None:
                    print('Cannot convert data type: %s' % data_type)
                    return {}  # don't know how to convert data atom
                # skip header & null-bytes, convert rest
                return {fieldname: conversion(data_atom[8:])}
            return parse_data_atom

        @classmethod
        def make_number_parser(cls, fieldname1, fieldname2):
            def _(data_atom):
                number_data = data_atom[8:14]
                numbers = struct.unpack('>HHH', number_data)
                # for some reason the first number is always irrelevant.
                return {fieldname1: numbers[1], fieldname2: numbers[2]}
            return _

        @classmethod
        def parse_id3v1_genre(cls, data_atom):
            # dunno why the genre is offset by -1 but this is how mutagen does it
            idx = struct.unpack('>H', data_atom[8:])[0] - 1
            if idx < len(ID3.ID3V1_GENRES):
                return {'genre': ID3.ID3V1_GENRES[idx]}
            return {'genre': None}

        @classmethod
        def parse_audio_sample_entry(cls, data):
            # this atom also contains the esds atom:
            # https://ffmpeg.org/doxygen/0.6/mov_8c-source.html
            # http://xhelmboyx.tripod.com/formats/mp4-layout.txt
            datafh = BytesIO(data)
            datafh.seek(16, os.SEEK_CUR) # jump over version and flags
            channels = struct.unpack('>H', datafh.read(2))[0]
            bit_depth = struct.unpack('>H', datafh.read(2))[0]
            datafh.seek(2, os.SEEK_CUR)  # jump over QT compr id & pkt size
            sr = struct.unpack('>I', datafh.read(4))[0]
            esds_atom_size = struct.unpack('>I', data[28:32])[0]
            esds_atom = BytesIO(data[36:36 + esds_atom_size])
            # http://sasperger.tistory.com/103
            esds_atom.seek(22, os.SEEK_CUR)  # jump over most data...
            max_br = struct.unpack('>I', esds_atom.read(4))[0] / 1000 # use
            avg_br = struct.unpack('>I', esds_atom.read(4))[0] / 1000 # kbit/s
            return {'channels': channels, 'samplerate': sr, 'bitrate': avg_br}

        @classmethod
        def parse_mvhd(cls, data):
            # http://stackoverflow.com/a/3639993/1191373
            walker = BytesIO(data)
            version = struct.unpack('b', walker.read(1))[0]
            flags = walker.read(3)
            if version == 0:  # uses 32 bit integers for timestamps
                walker.seek(8, os.SEEK_CUR) # jump over create & mod times
                time_scale = struct.unpack('>I', walker.read(4))[0]
                duration = struct.unpack('>I', walker.read(4))[0]
            else: # version == 1:  # uses 64 bit integers for timestamps
                walker.seek(16, os.SEEK_CUR) # jump over create & mod times
                time_scale = struct.unpack('>I', walker.read(4))[0]
                duration = struct.unpack('>q', walker.read(8))[0]
            return {'duration': float(duration) / time_scale}

        @classmethod
        def debug_atom(cls, data):
            print(data)  # use this function to inspect atoms in an atom tree
            return {}

    # The parser tree: Each key is an atom branch which is traversed if existing.
    # Leaves of the parser tree are callables which receive the atom data.
    # callables return {fieldname: value} which is applied to the tinytag instance.
    META_DATA_TREE = {b'moov': { b'udta': {b'meta': {b'ilst': {
        # see: http://atomicparsley.sourceforge.net/mpeg-4files.html
        b'\xa9alb': {b'data': Parser.make_data_atom_parser('album')},
        b'\xa9ART': {b'data': Parser.make_data_atom_parser('artist')},
        b'aART':    {b'data': Parser.make_data_atom_parser('albumartist')},
        # b'cpil':    {b'data': Parser.make_data_atom_parser('compilation')},
        b'disk':    {b'data': Parser.make_number_parser('disc', 'disc_total')},
        # b'\xa9wrt': {b'data': Parser.make_data_atom_parser('composer')},
        b'\xa9day': {b'data': Parser.make_data_atom_parser('year')},
        b'\xa9gen': {b'data': Parser.make_data_atom_parser('genre')},
        b'gnre':    {b'data': Parser.parse_id3v1_genre},
        b'\xa9nam': {b'data': Parser.make_data_atom_parser('title')},
        b'trkn':    {b'data': Parser.make_number_parser('track', 'track_total')},
        # b'covr':    {b'data': Parser.make_data_atom_parser('_image_data')},
    }}}}}

    # see: https://developer.apple.com/library/mac/documentation/QuickTime/QTFF/QTFFChap3/qtff3.html
    AUDIO_DATA_TREE = {
        b'moov': {
            b'mvhd': Parser.parse_mvhd,
            b'trak': {b'mdia': {b"minf": {b"stbl": {b"stsd": {b'mp4a':
                Parser.parse_audio_sample_entry
            }}}}}
        }
    }

    VERSIONED_ATOMS = set((b'meta', b'stsd'))  # those have an extra 4 byte header
    FLAGGED_ATOMS = set((b'stsd',))  # these also have an extra 4 byte header

    def _determine_duration(self, fh):
        return self._traverse_atoms(fh, path=self.AUDIO_DATA_TREE)

    def _parse_tag(self, fh):
        return self._traverse_atoms(fh, path=self.META_DATA_TREE)

    def _traverse_atoms(self, fh, path, indent=0, stop_pos=None, curr_path=None):
        header_size = 8
        atom_header = fh.read(header_size)
        while len(atom_header) == header_size:
            atom_size = struct.unpack('>I', atom_header[:4])[0] - header_size
            atom_type = atom_header[4:]
            if curr_path is None:  # keep track how we traversed in the tree
                curr_path = [atom_type]
            if atom_size <= 0:  # empty atom, jump to next one
                atom_header = fh.read(header_size)
                continue
            if DEBUG:
                print('%s pos: %d atom: %s len: %d' % (' ' * 4 * len(curr_path), fh.tell() - header_size, atom_type, atom_size + header_size))
            if atom_type in self.VERSIONED_ATOMS:  # jump atom version for now
                fh.seek(4, os.SEEK_CUR)
            if atom_type in self.FLAGGED_ATOMS:  # jump atom flags for now
                fh.seek(4, os.SEEK_CUR)
            sub_path = path.get(atom_type, None)
            # if the path leaf is a dict, traverse deeper into the tree:
            if issubclass(type(sub_path), MutableMapping):
                atom_end_pos = fh.tell() + atom_size
                self._traverse_atoms(fh, path=sub_path, stop_pos=atom_end_pos,
                                     curr_path=curr_path + [atom_type])
            # if the path-leaf is a callable, call it on the atom data
            elif callable(sub_path):
                for fieldname, value in sub_path(fh.read(atom_size)).items():
                    if DEBUG:
                        print(' ' * 4 * len(curr_path), 'FIELDNAME: ', fieldname)
                    if fieldname:
                        self._set_field(fieldname, value)
            # if no action was specified using dict or callable, jump over atom
            else:
                fh.seek(atom_size, os.SEEK_CUR)
            # check if we have reached the end of this branch:
            if stop_pos and fh.tell() >= stop_pos:
                return  # return to parent (next parent node in tree)
            atom_header = fh.read(header_size) # read next atom


class ID3(TinyTag):
    FRAME_ID_TO_FIELD = {  # Mapping from Frame ID to a field of the TinyTag
        'TRCK': 'track',  'TRK': 'track',
        'TYER': 'year',   'TYE': 'year',
        'TALB': 'album',  'TAL': 'album',
        'TPE1': 'artist', 'TP1': 'artist',
        'TIT2': 'title',  'TT2': 'title',
        'TCON': 'genre',  'TPOS': 'disc',
        'TPE2': 'albumartist',
    }
    _MAX_ESTIMATION_SEC = 30
    _CBR_DETECTION_FRAME_COUNT = 5
    _USE_XING_HEADER = True  # much faster, but can be deactivated for testing

    ID3V1_GENRES = [
        'Blues', 'Classic Rock', 'Country', 'Dance', 'Disco',
        'Funk', 'Grunge', 'Hip-Hop', 'Jazz', 'Metal', 'New Age', 'Oldies',
        'Other', 'Pop', 'R&B', 'Rap', 'Reggae', 'Rock', 'Techno', 'Industrial',
        'Alternative', 'Ska', 'Death Metal', 'Pranks', 'Soundtrack',
        'Euro-Techno', 'Ambient', 'Trip-Hop', 'Vocal', 'Jazz+Funk', 'Fusion',
        'Trance', 'Classical', 'Instrumental', 'Acid', 'House', 'Game',
        'Sound Clip', 'Gospel', 'Noise', 'AlternRock', 'Bass', 'Soul', 'Punk',
        'Space', 'Meditative', 'Instrumental Pop', 'Instrumental Rock',
        'Ethnic', 'Gothic','Darkwave', 'Techno-Industrial', 'Electronic',
        'Pop-Folk', 'Eurodance', 'Dream', 'Southern Rock', 'Comedy', 'Cult',
        'Gangsta', 'Top 40', 'Christian Rap', 'Pop/Funk', 'Jungle',
        'Native American', 'Cabaret', 'New Wave', 'Psychadelic', 'Rave',
        'Showtunes', 'Trailer', 'Lo-Fi', 'Tribal', 'Acid Punk', 'Acid Jazz',
        'Polka', 'Retro', 'Musical', 'Rock & Roll', 'Hard Rock',

        # Wimamp Extended Genres
        'Folk', 'Folk-Rock', 'National Folk', 'Swing', 'Fast Fusion', 'Bebob',
        'Latin', 'Revival', 'Celtic', 'Bluegrass', 'Avantgarde', 'Gothic Rock',
        'Progressive Rock', 'Psychedelic Rock', 'Symphonic Rock', 'Slow Rock',
        'Big Band', 'Chorus', 'Easy Listening', 'Acoustic', 'Humour', 'Speech',
        'Chanson', 'Opera', 'Chamber Music', 'Sonata', 'Symphony', 'Booty Bass',
        'Primus', 'Porn Groove', 'Satire', 'Slow Jam', 'Club', 'Tango', 'Samba',
        'Folklore', 'Ballad', 'Power Ballad', 'Rhythmic Soul', 'Freestyle',
        'Duet', 'Punk Rock', 'Drum Solo', 'A capella', 'Euro-House', 'Dance Hall',
        'Goa', 'Drum & Bass',

        # according to https://de.wikipedia.org/wiki/Liste_der_ID3v1-Genres:
        'Club-House', 'Hardcore Techno', 'Terror', 'Indie', 'BritPop',
        # don't use ethnic slur ("Negerpunk", WTF!)
        '',
        'Polsk Punk', 'Beat', 'Christian Gangsta Rap',
        'Heavy Metal', 'Black Metal', 'Contemporary Christian',
        'Christian Rock',
        # WinAmp 1.91
        'Merengue', 'Salsa', 'Thrash Metal', 'Anime', 'Jpop', 'Synthpop',
        # WinAmp 5.6
        'Abstract', 'Art Rock', 'Baroque', 'Bhangra', 'Big Beat', 'Breakbeat',
        'Chillout', 'Downtempo', 'Dub', 'EBM', 'Eclectic', 'Electro',
        'Electroclash', 'Emo', 'Experimental', 'Garage', 'Illbient',
        'Industro-Goth', 'Jam Band', 'Krautrock', 'Leftfield', 'Lounge',
        'Math Rock', 'New Romantic', 'Nu-Breakz', 'Post-Punk', 'Post-Rock',
        'Psytrance', 'Shoegaze', 'Space Rock', 'Trop Rock', 'World Music',
        'Neoclassical', 'Audiobook', 'Audio Theatre', 'Neue Deutsche Welle',
        'Podcast', 'Indie Rock', 'G-Funk', 'Dubstep', 'Garage Rock', 'Psybient',
    ]

    def __init__(self, filehandler, filesize):
        TinyTag.__init__(self, filehandler, filesize)
        # save position after the ID3 tag for duration mesurement speedup
        self._bytepos_after_id3v2 = 0

    @classmethod
    def set_estimation_precision(cls, estimation_in_seconds):
        cls._MAX_ESTIMATION_SEC = estimation_in_seconds

    # see this page for the magic values used in mp3:
    # http://www.mpgedit.org/mpgedit/mpeg_format/mpeghdr.htm
    samplerates = [
        [11025, 12000,  8000],  # MPEG 2.5
        [],                     # reserved
        [22050, 24000, 16000],  # MPEG 2
        [44100, 48000, 32000],  # MPEG 1
    ]
    v1l1 = [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 0]
    v1l2 = [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 0]
    v1l3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
    v2l1 = [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, 0]
    v2l2 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
    v2l3 = v2l2
    bitrate_by_version_by_layer = [
        [None, v2l3, v2l2, v2l1], # MPEG Version 2.5  # note that the layers go
        None,                     # reserved          # from 3 to 1 by design.
        [None, v2l3, v2l2, v2l1], # MPEG Version 2    # the first layer id is
        [None, v1l3, v1l2, v1l1], # MPEG Version 1    # reserved
    ]
    samples_per_frame = 1152  # the default frame size for mp3
    channels_per_channel_mode = [
        2,  # 00 Stereo
        2,  # 01 Joint stereo (Stereo)
        2,  # 10 Dual channel (2 mono channels)
        1,  # 11 Single channel (Mono)
    ]

    def _parse_xing_header(self, fh):
        # see: http://www.mp3-tech.org/programmer/sources/vbrheadersdk.zip
        fh.seek(4, os.SEEK_CUR) # read over Xing header
        header_flags = struct.unpack('>i', fh.read(4))[0]
        frames = byte_count = toc = vbr_scale = None
        if header_flags & 1: # FRAMES FLAG
            frames = struct.unpack('>i', fh.read(4))[0]
        if header_flags & 2: # BYTES FLAG
            byte_count = struct.unpack('>i', fh.read(4))[0]
        if header_flags & 4: # TOC FLAG
            toc = [struct.unpack('>i', fh.read(4))[0] for _ in range(100)]
        if header_flags & 8: # VBR SCALE FLAG
            vbr_scale = struct.unpack('>i', fh.read(4))[0]
        return frames, byte_count, toc, vbr_scale

    def _determine_duration(self, fh):
        max_estimation_frames = (ID3._MAX_ESTIMATION_SEC*44100) // ID3.samples_per_frame
        frame_size_accu = 0
        header_bytes = 4
        frames = 0  # count frames for determining mp3 duration
        bitrate_accu = 0  # add up bitrates to find average bitrate
        last_bitrates = []  # to detect CBR mp3s (multiple frames with same bitrates)
        # seek to first position after id3 tag (speedup for large header)
        fh.seek(self._bytepos_after_id3v2)
        while True:
            # reading through garbage until 11 '1' sync-bits are found
            b = fh.peek(4)
            if len(b) < 4:
                break  # EOF
            sync, conf, bitrate_freq, rest = struct.unpack('BBBB', b[0:4])
            br_id = (bitrate_freq >> 4) & 0x0F  # biterate id
            sr_id = (bitrate_freq >> 2) & 0x03  # sample rate id
            padding = 1 if bitrate_freq & 0x02 > 0 else 0
            mpeg_id = (conf >> 3) & 0x03
            layer_id = (conf >> 1) & 0x03
            channel_mode = (rest  >> 6) & 0x03
            self.channels = self.channels_per_channel_mode[channel_mode]
            # check for eleven 1s, validate bitrate and sample rate
            if not b[:2] > b'\xFF\xE0' or br_id > 14 or br_id == 0 or sr_id == 3:
                idx = b.find(b'\xFF', 1)  # invalid frame, find next sync header
                if idx == -1:
                    idx = len(b)  # not found: jump over the current peek buffer
                fh.seek(max(idx, 1), os.SEEK_CUR)
                continue
            try:
                self.samplerate = ID3.samplerates[mpeg_id][sr_id]
                frame_bitrate = ID3.bitrate_by_version_by_layer[mpeg_id][layer_id][br_id]
            except (IndexError, TypeError):
                raise TinyTagException('mp3 parsing failed')
            # There might be a xing header in the first frame that contains
            # all the info we need, otherwise parse multiple frames to find the
            # accurate average bitrate
            if frames == 0 and ID3._USE_XING_HEADER:
                xing_header_offset = b.find(b'Xing')
                if xing_header_offset != -1:
                    fh.seek(xing_header_offset, os.SEEK_CUR)
                    xframes, byte_count, toc, vbr_scale = self._parse_xing_header(fh)
                    if xframes is not None and byte_count is not None:
                        self.duration = xframes * ID3.samples_per_frame / float(self.samplerate)
                        self.bitrate = byte_count * 8 / self.duration
                        self.audio_offset = fh.tell()
                        return
                    continue

            frames += 1  # it's most probably an mp3 frame
            bitrate_accu += frame_bitrate
            if frames == 1:
                self.audio_offset = fh.tell()
            if frames <= ID3._CBR_DETECTION_FRAME_COUNT:
                last_bitrates.append(frame_bitrate)
            fh.seek(4, os.SEEK_CUR)  # jump over peeked bytes

            frame_length = (144000 * frame_bitrate) // self.samplerate + padding
            frame_size_accu += frame_length
            # if bitrate does not change over time its CBR
            is_cbr = frames == ID3._CBR_DETECTION_FRAME_COUNT and len(set(last_bitrates)) == 1

            if frames == max_estimation_frames or is_cbr:
                # try to estimate duration
                fh.seek(-128, 2)  # jump to last byte (leaving out id3v1 tag)
                audio_stream_size = fh.tell() - self.audio_offset
                est_frame_count = audio_stream_size / (frame_size_accu / float(frames))
                samples = est_frame_count * ID3.samples_per_frame
                self.duration = samples / float(self.samplerate)
                self.bitrate = bitrate_accu / frames
                return

            if frame_length > 1:  # jump over current frame body
                fh.seek(frame_length - header_bytes, os.SEEK_CUR)
        if self.samplerate:
            self.duration = frames * ID3.samples_per_frame / float(self.samplerate)

    def _parse_tag(self, fh):
        self._parse_id3v2(fh)
        if not self.has_all_tags() and self.filesize > 128:
            fh.seek(-128, os.SEEK_END)  # try parsing id3v1 in the last 128 bytes
            self._parse_id3v1(fh)

    def _parse_id3v2(self, fh):
        # for info on the specs, see: http://id3.org/Developer%20Information
        header = struct.unpack('3sBBB4B', _read(fh, 10))
        tag = codecs.decode(header[0], 'ISO-8859-1')
        # check if there is an ID3v2 tag at the beginning of the file
        if tag == 'ID3':
            major, rev = header[1:3]
            unsync = (header[3] & 0x80) > 0
            extended = (header[3] & 0x40) > 0
            experimental = (header[3] & 0x20) > 0
            footer = (header[3] & 0x10) > 0
            size = self._calc_size(header[4:8], 7)
            self._bytepos_after_id3v2 = size
            parsed_size = 0
            if extended:  # just read over the extended header.
                size_bytes = struct.unpack('4B', _read(fh, 6)[0:4])
                extd_size = self._calc_size(size_bytes, 7)
                fh.seek(extd_size - 6, os.SEEK_CUR)  # jump over extended_header
            while parsed_size < size:
                frame_size = self._parse_frame(fh, id3version=major)
                if frame_size == 0:
                    break
                parsed_size += frame_size

    def _parse_id3v1(self, fh):
        if fh.read(3) == b'TAG':  # check if this is an ID3 v1 tag
            asciidecode = lambda x: self._unpad(codecs.decode(x, 'latin1'))
            fields = fh.read(30 + 30 + 30 + 4 + 30 + 1)
            self._set_field('title', fields[:30], transfunc=asciidecode)
            self._set_field('artist', fields[30:60], transfunc=asciidecode)
            self._set_field('album', fields[60:90], transfunc=asciidecode)
            self._set_field('year', fields[90:94], transfunc=asciidecode)
            comment = fields[94:124]
            if b'\x00\x00' < comment[-2:] < b'\x01\x00':
                self._set_field('track', str(ord(comment[-1:])))
            genre_id = ord(fields[124:125])
            if genre_id < len(ID3.ID3V1_GENRES):
                self.genre = ID3.ID3V1_GENRES[genre_id]

    def _parse_frame(self, fh, id3version=False):
        encoding = 'ISO-8859-1'  # default encoding used in most mp3 tags
        # ID3v2.2 especially ugly. see: http://id3.org/id3v2-00
        frame_header_size = 6 if id3version == 2 else 10
        frame_size_bytes = 3 if id3version == 2 else 4
        binformat = '3s3B' if id3version == 2 else '4s4B2B'
        bits_per_byte = 7 if id3version == 4 else 8  # only id3v2.4 is synchsafe
        frame_header_data = fh.read(frame_header_size)
        if len(frame_header_data) == 0:
            return 0
        frame = struct.unpack(binformat, frame_header_data)
        frame_id = self._decode_string(frame[0])
        frame_size = self._calc_size(frame[1:1+frame_size_bytes], bits_per_byte)
        parsable = frame_id in ID3.FRAME_ID_TO_FIELD or frame_id == 'APIC'
        if frame_size > 0:
            # flags = frame[1+frame_size_bytes:] # dont care about flags.
            if not parsable:  # jump over unparsable frames
                fh.seek(frame_size, os.SEEK_CUR)
                return frame_size
            content = fh.read(frame_size)
            fieldname = ID3.FRAME_ID_TO_FIELD.get(frame_id)
            if fieldname:
                self._set_field(fieldname, content, self._decode_string)
            elif frame_id == 'APIC' and self._load_image:
                # See section 4.14: http://id3.org/id3v2.4.0-frames
                mimetype_end_pos = content[1:].index(b'\x00')+1
                desc_start_pos = mimetype_end_pos + 2
                desc_end_pos = desc_start_pos + content[desc_start_pos:].index(b'\x00')
                if content[desc_end_pos:desc_end_pos+1] == b'\x00':
                    desc_end_pos += 1 # the description ends with 1 or 2 null bytes
                self._image_data = content[desc_end_pos:]
            return frame_size
        return 0

    def _decode_string(self, b):
        # it's not my fault, this is the spec.
        try:
            first_byte = b[:1]
            if first_byte == b'\x00':
                return self._unpad(codecs.decode(b[1:], 'ISO-8859-1'))
            elif first_byte == b'\x01':
                # read byte order mark to determine endianess
                encoding = 'UTF-16be' if b[1:3] == b'\xfe\xff' else 'UTF-16le'
                # strip the bom and optional null bytes
                bytestr = b[3:-1] if len(b) % 2 == 0 else b[3:]
                return self._unpad(codecs.decode(bytestr, encoding))
            elif first_byte == b'\x02':
                # strip optional null byte
                bytestr = b[1:-1] if len(b) % 2 == 0 else b[1:]
                return self._unpad(codecs.decode(bytestr, 'UTF-16le'))
            elif first_byte == b'\x03':
                return codecs.decode(b[1:], 'UTF-8')
            return self._unpad(codecs.decode(b, 'ISO-8859-1'))
        except UnicodeDecodeError:
            raise TinyTagException('Error decoding ID3 Tag!')

    def _calc_size(self, bytestr, bits_per_byte):
        # length of some mp3 header fields is described
        # by "7-bit-bytes" or sometimes 8-bit bytes...
        ret = 0
        for b in bytestr:
            ret <<= bits_per_byte
            ret += b
        return ret


class Ogg(TinyTag):
    def __init__(self, filehandler, filesize):
        TinyTag.__init__(self, filehandler, filesize)
        self._tags_parsed = False
        self._max_samplenum = 0  # maximum sample position ever read

    def _determine_duration(self, fh):
        MAX_PAGE_SIZE = 65536  # https://xiph.org/ogg/doc/libogg/ogg_page.html
        if not self._tags_parsed:
            self._parse_tag(fh)  # determine sample rate
            fh.seek(0)           # and rewind to start
        if self.filesize > MAX_PAGE_SIZE:
            fh.seek(-MAX_PAGE_SIZE, 2)  # go to last possible page position
        while True:
            b = fh.peek(4)
            if len(b) == 0:
                return  # EOF
            if b[:4] == b'OggS':  # look for an ogg header
                for packet in self._parse_pages(fh):
                    pass  # parse all remaining pages
                self.duration = self._max_samplenum / float(self.samplerate)
            else:
                idx = b.find(b'OggS')  # try to find header in peeked data
                seekpos = idx if idx != -1 else len(b) - 3
                fh.seek(max(seekpos, 1), os.SEEK_CUR)

    def _parse_tag(self, fh):
        page_start_pos = fh.tell()  # set audio_offest later if its audio data
        for packet in self._parse_pages(fh):
            walker = BytesIO(packet)
            if packet[0:7] == b"\x01vorbis":
                (channels, self.samplerate, max_bitrate, bitrate,
                 min_bitrate) = struct.unpack("<B4i", packet[11:28])
                if not self.audio_offset:
                    self.bitrate = bitrate / 1024
                    self.audio_offset = page_start_pos
            elif packet[0:7] == b"\x03vorbis":
                walker.seek(7, os.SEEK_CUR)  # jump over header name
                self._parse_vorbis_comment(walker)
            elif packet[0:8] == b'OpusHead':  # parse opus header
                # https://www.videolan.org/developers/vlc/modules/codec/opus_header.c
                # https://mf4.xiph.org/jenkins/view/opus/job/opusfile-unix/ws/doc/html/structOpusHead.html
                walker.seek(8, os.SEEK_CUR)  # jump over header name
                (version, ch, _, sr, _, _) = struct.unpack("<BBHIHB", walker.read(11))
                if (version & 0xF0) == 0:  # only major version 0 supported
                    self.channels = ch
                    self.samplerate = sr
            elif packet[0:8] == b'OpusTags':  # parse opus metadata:
                walker.seek(8, os.SEEK_CUR)  # jump over header name
                self._parse_vorbis_comment(walker)
            else:
                break
            page_start_pos = fh.tell()

    def _parse_vorbis_comment(self, fh):
        # for the spec, see: http://xiph.org/vorbis/doc/v-comment.html
        # discnumber tag based on: https://en.wikipedia.org/wiki/Vorbis_comment
        comment_type_to_attr_mapping = {
            'album': 'album',
            'albumartist': 'albumartist',
            'title': 'title',
            'artist': 'artist',
            'date': 'year',
            'tracknumber': 'track',
            'discnumber': 'disc',
            'genre': 'genre'
        }
        vendor_length = struct.unpack('I', fh.read(4))[0]
        fh.seek(vendor_length, os.SEEK_CUR)  # jump over vendor
        elements = struct.unpack('I', fh.read(4))[0]
        for i in range(elements):
            length = struct.unpack('I', fh.read(4))[0]
            keyvalpair = codecs.decode(fh.read(length), 'UTF-8')
            if '=' in keyvalpair:
                splitidx = keyvalpair.index('=')
                key, value = keyvalpair[:splitidx], keyvalpair[splitidx+1:]
                fieldname = comment_type_to_attr_mapping.get(key.lower())
                if fieldname:
                    self._set_field(fieldname, value)

    def _parse_pages(self, fh):
        # for the spec, see: https://wiki.xiph.org/Ogg
        previous_page = b''  # contains data from previous (continuing) pages
        header_data = fh.read(27)  # read ogg page header
        while len(header_data) != 0:
            header = struct.unpack('<4sBBqIIiB', header_data)
            oggs, version, flags, pos, serial, pageseq, crc, segments = header
            self._max_samplenum = max(self._max_samplenum, pos)
            if oggs != b'OggS' or version != 0:
                raise TinyTagException('Not a valid ogg file!')
            segsizes = struct.unpack('B'*segments, fh.read(segments))
            total = 0
            for segsize in segsizes:  # read all segments
                total += segsize
                if total < 255:  # less than 255 bytes means end of page
                    yield previous_page + fh.read(total)
                    previous_page = b''
                    total = 0
            if total != 0:
                if total % 255 == 0:
                    previous_page += fh.read(total)
                else:
                    yield previous_page + fh.read(total)
                    previous_page = b''
            header_data = fh.read(27)


class Wave(TinyTag):
    def __init__(self, filehandler, filesize):
        TinyTag.__init__(self, filehandler, filesize)
        self._duration_parsed = False

    def _determine_duration(self, fh):
        # see: https://ccrma.stanford.edu/courses/422/projects/WaveFormat/
        # and: https://en.wikipedia.org/wiki/WAV
        riff, size, fformat = struct.unpack('4sI4s', fh.read(12))
        if riff != b'RIFF' or fformat != b'WAVE':
            raise TinyTagException('not a wave file!')
        channels, bitdepth = 2, 16  # assume CD quality
        chunk_header = fh.read(8)
        while len(chunk_header) == 8:
            subchunkid, subchunksize = struct.unpack('4sI', chunk_header)
            if subchunkid == b'fmt ':
                _, channels, self.samplerate = struct.unpack('HHI', fh.read(8))
                _, _, bitdepth = struct.unpack('<IHH', fh.read(8))
                self.bitrate = self.samplerate * channels * bitdepth / 1024
            elif subchunkid == b'data':
                self.duration = float(subchunksize)/channels/self.samplerate/(bitdepth/8)
                self.audio_offest = fh.tell() - 8  # rewind to data header
                fh.seek(subchunksize, 1)
            elif subchunkid == b'id3 ' or subchunkid == b'ID3 ':
                id3 = ID3(fh, 0)
                id3._parse_id3v2(fh)
                self.update(id3)
            else:  # some other chunk, just skip the data
                fh.seek(subchunksize, 1)
            chunk_header = fh.read(8)
        self._duration_parsed = True

    def _parse_tag(self, fh):
        if not self._duration_parsed:
            self._determine_duration(fh)  # parse_whole file to determine tags :(


class Flac(TinyTag):
    METADATA_STREAMINFO = 0
    METADATA_VORBIS_COMMENT = 4

    def load(self, tags, duration, image=False):
        if self._filehandler.read(4) != b'fLaC':
            raise TinyTagException('Invalid flac header')
        self._determine_duration(self._filehandler, skip_tags=not tags)

    def _determine_duration(self, fh, skip_tags=False):
        # for spec, see https://xiph.org/flac/ogg_mapping.html
        header_data = fh.read(4)
        while len(header_data):
            meta_header = struct.unpack('B3B', header_data)
            block_type = meta_header[0] & 0x7f
            is_last_block = meta_header[0] & 0x80
            size = self._bytes_to_int(meta_header[1:4])
            # http://xiph.org/flac/format.html#metadata_block_streaminfo
            if block_type == Flac.METADATA_STREAMINFO:
                stream_info_header = fh.read(size)
                if len(stream_info_header) < 34:  # invalid streaminfo
                    break
                header = struct.unpack('HH3s3s8B16s', stream_info_header)
                # From the ciph documentation:
                # py | <bits>
                #----------------------------------------------
                # H  | <16>  The minimum block size (in samples)
                # H  | <16>  The maximum block size (in samples)
                # 3s | <24>  The minimum frame size (in bytes)
                # 3s | <24>  The maximum frame size (in bytes)
                # 8B | <20>  Sample rate in Hz.
                #    | <3>   (number of channels)-1.
                #    | <5>   (bits per sample)-1.
                #    | <36>  Total samples in stream.
                # 16s| <128> MD5 signature
                #
                min_blk, max_blk, min_frm, max_frm = header[0:4]
                min_frm = self._bytes_to_int(struct.unpack('3B', min_frm))
                max_frm = self._bytes_to_int(struct.unpack('3B', max_frm))
                #                 channels-
                #                          `.  bits      total samples
                # |----- samplerate -----| |-||----| |---------~   ~----|
                # 0000 0000 0000 0000 0000 0000 0000 0000 0000      0000
                # #---4---# #---5---# #---6---# #---7---# #--8-~   ~-12-#
                self.samplerate = self._bytes_to_int(header[4:7]) >> 4
                channels = ((header[6] >> 1) & 0x07) + 1
                bit_depth = ((header[6] & 1) << 4) + ((header[7] & 0xF0) >> 4)
                bit_depth = (bit_depth + 1)
                total_sample_bytes = [(header[7] & 0x0F)] + list(header[8:12])
                total_samples = self._bytes_to_int(total_sample_bytes)
                md5 = header[12:]
                self.duration = float(total_samples) / self.samplerate
                if self.duration > 0:
                    self.bitrate = self.filesize / self.duration * 8 / 1024
                #return
            elif block_type == Flac.METADATA_VORBIS_COMMENT and not skip_tags:
                oggtag = Ogg(fh, 0)
                oggtag._parse_vorbis_comment(fh)
                self.update(oggtag)
            elif block_type >= 127:
                return # invalid block type
            else:
                fh.seek(size, 1)  # seek over this block

            if is_last_block:
                break
            else:
                header_data = fh.read(4)


class Wma(TinyTag):
    ASF_CONTENT_DESCRIPTION_OBJECT = b'3&\xb2u\x8ef\xcf\x11\xa6\xd9\x00\xaa\x00b\xcel'
    ASF_EXTENDED_CONTENT_DESCRIPTION_OBJECT = b'@\xa4\xd0\xd2\x07\xe3\xd2\x11\x97\xf0\x00\xa0\xc9^\xa8P'
    STREAM_BITRATE_PROPERTIES_OBJECT = b'\xceu\xf8{\x8dF\xd1\x11\x8d\x82\x00`\x97\xc9\xa2\xb2'
    ASF_FILE_PROPERTY_OBJECT = b'\xa1\xdc\xab\x8cG\xa9\xcf\x11\x8e\xe4\x00\xc0\x0c Se'
    ASF_STREAM_PROPERTIES_OBJECT = b'\x91\x07\xdc\xb7\xb7\xa9\xcf\x11\x8e\xe6\x00\xc0\x0c Se'
    STREAM_TYPE_ASF_AUDIO_MEDIA = b'@\x9ei\xf8M[\xcf\x11\xa8\xfd\x00\x80_\\D+'
    # see:
    # http://web.archive.org/web/20131203084402/http://msdn.microsoft.com/en-us/library/bb643323.aspx
    # and (japanese, but none the less helpful)
    # http://uguisu.skr.jp/Windows/format_asf.html

    def __init__(self, filehandler, filesize):
        TinyTag.__init__(self, filehandler, filesize)
        self.__tag_parsed = False

    def _determine_duration(self, fh):
        if not self.__tag_parsed:
            self._parse_tag(fh)

    def read_blocks(self, fh, blocks):
        # blocks are a list(tuple('fieldname', byte_count, cast_int), ...)
        decoded = {}
        for block in blocks:
            val = fh.read(block[1])
            if block[2]:
                val = self._bytes_to_int_le(val)
            decoded[block[0]] = val
        return decoded

    def __bytes_to_guid(self, obj_id_bytes):
        return '-'.join([
            hex(self._bytes_to_int_le(obj_id_bytes[:-12]))[2:].zfill(6),
            hex(self._bytes_to_int_le(obj_id_bytes[-12:-10]))[2:].zfill(4),
            hex(self._bytes_to_int_le(obj_id_bytes[-10:-8]))[2:].zfill(4),
            hex(self._bytes_to_int(obj_id_bytes[-8:-6]))[2:].zfill(4),
            hex(self._bytes_to_int(obj_id_bytes[-6:]))[2:].zfill(12),
        ])

    def __decode_string(self, bytestring):
        return self._unpad(codecs.decode(bytestring, 'utf-16'))

    def __decode_ext_desc(self, value_type, value):
        ''' decode ASF_EXTENDED_CONTENT_DESCRIPTION_OBJECT values'''
        if value_type == 0:  # Unicode string
            return self.__decode_string(value)
        elif value_type == 1:  # BYTE array
            return value
        elif 1 < value_type < 6:  # DWORD / QWORD / WORD
            return self._bytes_to_int_le(value)

    def _parse_tag(self, fh):
        self.__tag_parsed = True
        guid = fh.read(16) # 128 bit GUID
        if guid != b'0&\xb2u\x8ef\xcf\x11\xa6\xd9\x00\xaa\x00b\xcel':
            return # not a valid ASF container! see: http://www.garykessler.net/library/file_sigs.html
        size = struct.unpack('Q', fh.read(8))[0]
        obj_count = struct.unpack('I', fh.read(4))[0]
        if fh.read(2) != b'\x01\x02':
            # http://web.archive.org/web/20131203084402/http://msdn.microsoft.com/en-us/library/bb643323.aspx#_Toc521913958
            return # not a valid asf header!
        while True:
            object_id = fh.read(16)
            object_size = self._bytes_to_int_le(fh.read(8))
            if object_size == 0 or object_size > self.filesize:
                break  # invalid object, stop parsing.
            if object_id == Wma.ASF_CONTENT_DESCRIPTION_OBJECT:
                len_blocks = self.read_blocks(fh, [
                    ('title_length', 2, True),
                    ('author_length', 2, True),
                    ('copyright_length', 2, True),
                    ('description_length', 2, True),
                    ('rating_length', 2, True),
                ])
                data_blocks = self.read_blocks(fh, [
                    ('title', len_blocks['title_length'], False),
                    ('artist', len_blocks['author_length'], False),
                    ('', len_blocks['copyright_length'], True),
                    ('', len_blocks['description_length'], True),
                    ('', len_blocks['rating_length'], True),
                ])
                for field_name, bytestring in data_blocks.items():
                    if field_name:
                        self._set_field(field_name, bytestring, self.__decode_string)
            elif object_id == Wma.ASF_EXTENDED_CONTENT_DESCRIPTION_OBJECT:
                mapping = {
                    'WM/TrackNumber': 'track',
                    'WM/PartOfSet': 'disc',
                    'WM/Year': 'year',
                    'WM/AlbumArtist': 'albumartist',
                    'WM/Genre': 'genre',
                    'WM/AlbumTitle': 'album',
                }
                # see: http://web.archive.org/web/20131203084402/http://msdn.microsoft.com/en-us/library/bb643323.aspx#_Toc509555195
                descriptor_count = self._bytes_to_int_le(fh.read(2))
                for _ in range(descriptor_count):
                    name_len = self._bytes_to_int_le(fh.read(2))
                    name = self.__decode_string(fh.read(name_len))
                    value_type = self._bytes_to_int_le(fh.read(2))
                    value_len = self._bytes_to_int_le(fh.read(2))
                    value = fh.read(value_len)
                    field_name = mapping.get(name)
                    if field_name:
                        field_value = self.__decode_ext_desc(value_type, value)
                        self._set_field(field_name, field_value)
            elif object_id == Wma.ASF_FILE_PROPERTY_OBJECT:
                blocks = self.read_blocks(fh, [
                    ('file_id', 16, False),
                    ('file_size', 8, False),
                    ('creation_date', 8, True),
                    ('data_packets_count', 8, True),
                    ('play_duration', 8, True),
                    ('send_duration', 8, True),
                    ('preroll', 8, True),
                    ('flags', 4, False),
                    ('minimum_data_packet_size', 4, True),
                    ('maximum_data_packet_size', 4, True),
                    ('maximum_bitrate', 4, False),
                ])
                self.duration = blocks.get('play_duration') / float(10000000)
            elif object_id == Wma.ASF_STREAM_PROPERTIES_OBJECT:
                blocks = self.read_blocks(fh, [
                    ('stream_type', 16, False),
                    ('error_correction_type', 16, False),
                    ('time_offset', 8, True),
                    ('type_specific_data_length', 4, True),
                    ('error_correction_data_length', 4, True),
                    ('flags', 2, True),
                    ('reserved', 4, False)
                ])
                already_read = 0
                if blocks['stream_type'] == Wma.STREAM_TYPE_ASF_AUDIO_MEDIA:
                    stream_info = self.read_blocks(fh, [
                        ('codec_id_format_tag', 2, True),
                        ('number_of_channels', 2, True),
                        ('samples_per_second', 4, True),
                        ('avg_bytes_per_second', 4, True),
                        ('block_alignment', 2, True),
                        ('bits_per_sample', 2, True),
                    ])
                    self.samplerate = stream_info['samples_per_second']
                    self.bitrate = stream_info['avg_bytes_per_second'] * 8 / float(1000)
                    already_read = 16
                fh.seek(blocks['type_specific_data_length'] - already_read, os.SEEK_CUR)
                fh.seek(blocks['error_correction_data_length'], os.SEEK_CUR)
            else:
                fh.seek(object_size - 24, os.SEEK_CUR) # read over onknown object ids
