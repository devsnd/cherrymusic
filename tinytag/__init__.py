#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# tinytag - an audio meta info reader
# Copyright (c) 2014 Tom Wallroth
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

import codecs
import struct
import os

__version__ = '0.3.0'


class TinyTag(object):
    """Base class for all tag types"""
    def __init__(self):
        self.track = None
        self.track_total = None
        self.title = None
        self.artist = None
        self.album = None
        self.year = None
        self.length = 0

    def has_all_tags(self):
        """check if all tags are already defined. Useful for ID3 tags
        since multiple kinds of tags can be in one audio file
        """
        return all((self.track, self.track_total, self.title,
                    self.artist, self.album, self.year))

    @classmethod
    def get(cls, filename, tags=True, length=True):
        """choose which tag reader should be used by file extension"""
        if not os.path.getsize(filename) > 0:
            return TinyTag()
        if filename.lower().endswith('.mp3'):
            with open(filename, 'rb') as af:
                return ID3(af, tags=tags, length=length)
        elif filename.lower().endswith(('.oga', '.ogg')):
            with open(filename, 'rb') as af:
                return Ogg(af, tags=tags, length=length)
        elif filename.lower().endswith(('.wav')):
            with open(filename, 'rb') as af:
                return Wave(af, tags=tags, length=length)
        elif filename.lower().endswith(('.flac')):
            with open(filename, 'rb') as af:
                return Flac(af, tags=tags, length=length)
        else:
            raise LookupError('No tag reader found to support filetype!')

    def __str__(self):
        return str(self.__dict__)

    def load(self, filehandler, tags, length):
        """default behavior of all tags. This method is called in the
        constructors of all tag readers
        """
        if tags:
            self._parse_tag(filehandler)
            filehandler.seek(0)
        if length:
            self._determine_length(filehandler)

    def _set_field(self, fieldname, bytestring, transfunc=None):
        """convienience function to set fields of the tinytag by name.
        the payload (bytestring) can be changed using the transfunc"""
        if getattr(self, fieldname):
            return
        if transfunc:
            setattr(self, fieldname, transfunc(bytestring))
        else:
            setattr(self, fieldname, bytestring)

    def _determine_length(self, fh):
        raise NotImplementedError()

    def _parse_tag(self, fh):
        raise NotImplementedError()

    def update(self, other):
        """update the values of this tag with the values from another tag"""
        for key in ['track', 'track_total', 'title', 'artist',
                    'album', 'year', 'length']:
            if not getattr(self, key) and getattr(other, key):
                setattr(self, key, getattr(other, key))


class ID3(TinyTag):
    FID_TO_FIELD = {  # Mapping from Frame ID to a field of the TinyTag
        'TRCK': 'track',  'TRK': 'track',
        'TYER': 'year',   'TYE': 'year',
        'TALB': 'album',  'TAL': 'album',
        'TPE1': 'artist', 'TP1': 'artist',
        'TIT2': 'title',  'TT2': 'title',
    }

    def __init__(self, filehandler, tags=True, length=True):
        TinyTag.__init__(self)
        self.load(filehandler, tags=tags, length=length)

    def _determine_length(self, fh):
        max_estimation_sec = 30
        max_estimation_frames = (max_estimation_sec*44100) // 1152
        frame_size_mean = 0
        # set sample rate from first found frame later, default to 44khz
        file_sample_rate = 44100
        # see this page for the magic values used in mp3:
        # http://www.mpgedit.org/mpgedit/mpeg_format/mpeghdr.htm
        bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192,
                    224, 256, 320]
        samplerates = [44100, 48000, 32000]
        header_bytes = 4
        frames = 0  # count frames for determining mp3 length
        while True:
            # reading through garbage until 12 '1' bits are found
            b = fh.read(1)
            if len(b) == 0:
                break
            if b == b'\xff':
                b = fh.read(1)
                if b > b'\xf0':
                    bitrate_freq, rest = struct.unpack('BB', fh.read(2))
                    br_id = (bitrate_freq & 0xf0) >> 4  # biterate id
                    sr_id = (bitrate_freq & 0x03) >> 2  # sample rate id
                    # check if the values aren't just random
                    if br_id == 15 or br_id == 0 or sr_id == 3:
                        #invalid frame! roll back to last position
                        fh.seek(-2, os.SEEK_CUR)
                        continue
                    frames += 1  # it's most probably an mp3 frame
                    bitrate = bitrates[br_id]
                    samplerate = samplerates[sr_id]
                    if frames == 1:
                        file_sample_rate = samplerate
                    padding = 1 if bitrate_freq & 0x02 > 0 else 0
                    frame_length = (144000 * bitrate) // samplerate + padding
                    frame_size_mean += frame_length
                    if frames == max_estimation_frames:
                        # try to estimate length
                        fh.seek(-1, 2) # jump to last byte
                        estimated_frame_count = fh.tell() / (frame_size_mean / frames)
                        samples = estimated_frame_count * 1152
                        self.length = samples/float(file_sample_rate)
                        return
                    if frame_length > 1:
                        # jump over current frame body
                        fh.seek(frame_length - header_bytes, os.SEEK_CUR)
        samples = frames * 1152  # 1152 is the default frame size for mp3
        self.length = samples/float(file_sample_rate)

    def _parse_tag(self, fh):
        self._parse_id3v2(fh)
        if not self.has_all_tags():  # try to get more info using id3v1
            fh.seek(-128, 2)  # id3v1 occuppies the last 128 bytes
            self._parse_id3v1(fh)

    def _parse_id3v2(self, fh):
        # for info on the specs, see: http://id3.org/Developer%20Information
        header = struct.unpack('3sBBB4B', fh.read(10))
        tag = codecs.decode(header[0], 'ISO-8859-1')
        # check if there is an ID3v2 tag at the beginning of the file
        if tag == 'ID3':
            major, rev = header[1:3]
            unsync = (header[3] & 0x80) > 0
            extended = (header[3] & 0x40) > 0
            experimental = (header[3] & 0x20) > 0
            footer = (header[3] & 0x10) > 0
            size = self._calc_size_7bit_bytes(header[4:9])
            parsed_size = 0
            if extended:  # just read over the extended header.
                size_bytes = struct.unpack('4B', fh.read(6)[0:4])
                extd_size = self._calc_size_7bit_bytes(size_bytes)
                fh.read(extd_size - 6)
            while parsed_size < size:
                is_id3_v22 = major == 2
                frame_size = self._parse_frame(fh, is_v22=is_id3_v22)
                if frame_size == 0:
                    break
                parsed_size += frame_size

    def _parse_id3v1(self, fh):
        if fh.read(3) == b'TAG':  # check if this is an ID3 v1 tag
            asciidecode = lambda x: self._unpad(codecs.decode(x, 'ASCII'))
            self._set_field('title', fh.read(30), transfunc=asciidecode)
            self._set_field('artist', fh.read(30), transfunc=asciidecode)
            self._set_field('album', fh.read(30), transfunc=asciidecode)
            self._set_field('year', fh.read(4), transfunc=asciidecode)
            comment = fh.read(30)
            if b'\x00\x00' < comment[-2:] < b'\x01\x00':
                self._set_field('track', str(ord(comment[-1:])))

    def _parse_frame(self, fh, is_v22=False):
        encoding = 'ISO-8859-1'  # default encoding used in most mp3 tags
        # ID3v2.2 especially ugly. see: http://id3.org/id3v2-00
        frame_header_size = 6 if is_v22 else 10
        frame_size_bytes = 3 if is_v22 else 4
        binformat = '3s3B' if is_v22 else '4s4B2B'
        frame_header_data = fh.read(frame_header_size)
        if len(frame_header_data) == 0:
            return 0
        frame = struct.unpack(binformat, frame_header_data)
        frame_id = self._decode_string(frame[0])
        frame_size = self._calc_size_7bit_bytes(frame[1:1+frame_size_bytes])
        if frame_size > 0:
            # flags = frame[1+frame_size_bytes:] # dont care about flags.
            content = fh.read(frame_size)
            fieldname = ID3.FID_TO_FIELD.get(frame_id)
            if fieldname:
                if fieldname == 'track':
                    self._parse_track(content)
                else:
                    self._set_field(fieldname, content, self._decode_string)
            return frame_size
        return 0

    def _decode_string(self, b):
        # it's not my fault, this is the spec.
        if b[:1] == b'\x00':
            return self._unpad(codecs.decode(b[1:], 'ISO-8859-1'))
        if b[0:3] == b'\x01\xff\xfe':
            bytestr = b[3:-1] if len(b) % 2 == 0 else b[3:]
            return codecs.decode(bytestr, 'UTF-16')
        return self._unpad(codecs.decode(b, 'ISO-8859-1'))

    def _unpad(self, s):
        # strings in mp3 _can_ be terminated with a zero byte at the end
        return s[:s.index('\x00')] if '\x00' in s else s

    def _parse_track(self, b):
        track = self._decode_string(b)
        track_total = None
        if '/' in track:
            track, track_total = track.split('/')
        self._set_field('track', track)
        self._set_field('track_total', track_total)

    def _calc_size_7bit_bytes(self, bytestr):
        ret = 0             # length of mp3 header fields is described
        for b in bytestr:   # by some "7-bit-bytes". The most significant
            ret <<= 7       # bit is always set to zero, so it has to be
            ret += b & 127  # removed.
        return ret          #


class StringWalker(object):
    """file obj like string. probably there are buildins doing this already"""
    def __init__(self, string):
        self.string = string

    def read(self, length):
        retstring, self.string = self.string[:length], self.string[length:]
        return retstring


class Ogg(TinyTag):
    def __init__(self, filehandler, tags=True, length=True):
        TinyTag.__init__(self)
        self._tags_parsed = False
        self._max_samplenum = 0  # maximum sample position ever read
        self.load(filehandler, tags=tags, length=length)

    def _determine_length(self, fh):
        if not self._tags_parsed:
            self._parse_tag(fh)  # parse_whole file to determine length :(

    def _parse_tag(self, fh):
        sample_rate = 44100  # default samplerate 44khz, but update later
        for packet in self._parse_pages(fh):
            walker = StringWalker(packet)
            head = walker.read(7)
            if head == b"\x01vorbis":
                (channels, sample_rate, max_bitrate, nominal_bitrate,
                 min_bitrate) = struct.unpack("<B4i", packet[11:28])
            elif head == b"\x03vorbis":
                self._parse_vorbis_comment(walker)
        self.length = self._max_samplenum / float(sample_rate)

    def _parse_vorbis_comment(self, fh):
        # for the spec, see: http://xiph.org/vorbis/doc/v-comment.html
        mapping = {'album': 'album', 'title': 'title', 'artist': 'artist',
                   'date': 'year', 'tracknumber': 'track'}
        vendor_length = struct.unpack('I', fh.read(4))[0]
        vendor = fh.read(vendor_length)
        elements = struct.unpack('I', fh.read(4))[0]
        for i in range(elements):
            length = struct.unpack('I', fh.read(4))[0]
            keyvalpair = codecs.decode(fh.read(length), 'UTF-8')
            if '=' in keyvalpair:
                splitidx = keyvalpair.index('=')
                key, value = keyvalpair[:splitidx], keyvalpair[splitidx+1:]
                fieldname = mapping.get(key.lower())
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
                break  # not a valid ogg file
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
    def __init__(self, filename, tags=True, length=True):
        TinyTag.__init__(self)
        self._length_parsed = False
        self.load(filename, tags=tags, length=length)

    def _determine_length(self, fh):
        # see: https://ccrma.stanford.edu/courses/422/projects/WaveFormat/
        # and: https://en.wikipedia.org/wiki/WAV
        riff, size, fformat = struct.unpack('4sI4s', fh.read(12))
        if riff != b'RIFF' or fformat != b'WAVE':
            print('not a wave file!')
        channels, samplerate, bitdepth = 2, 44100, 16  # assume CD quality
        chunk_header = fh.read(8)
        while len(chunk_header) > 0:
            subchunkid, subchunksize = struct.unpack('4sI', chunk_header)
            if subchunkid == b'fmt ':
                _, channels, samplerate = struct.unpack('HHI', fh.read(8))
                _, _, bitdepth = struct.unpack('<IHH', fh.read(8))
            elif subchunkid == b'data':
                self.length = subchunksize/channels/samplerate/(bitdepth/8)
                fh.seek(subchunksize, 1)
            elif subchunkid == b'id3 ' or subchunkid == b'ID3 ':
                id3 = ID3(fh, tags=False, length=False)
                id3._parse_id3v2(fh)
                self.update(id3)
            else:  # some other chunk, just skip the data
                fh.seek(subchunksize, 1)
            chunk_header = fh.read(8)
        self._length_parsed = True

    def _parse_tag(self, fh):
        if not self._length_parsed:
            self._determine_length(fh)  # parse_whole file to determine tags :(


class Flac(TinyTag):
    def __init__(self, filename, tags=True, length=True):
        TinyTag.__init__(self)
        self.load(filename, tags=tags, length=length)

    def load(self, filehandler, tags, length):
        if filehandler.read(4) != b'fLaC':
            return  # not a flac file!
        if tags:
            self._parse_tag(filehandler)
            filehandler.seek(4)
        if length:
            self._determine_length(filehandler)

    def _determine_length(self, fh):
        # for spec, see https://xiph.org/flac/ogg_mapping.html
        header_data = fh.read(4)
        while len(header_data):
            meta_header = struct.unpack('B3B', header_data)
            size = self._bytes_to_int(meta_header[1:4])
            if meta_header[0] == 0:  # STREAMINFO
                header = struct.unpack('HH3s3s8B16s', fh.read(size))
                min_blk, max_blk, min_frm, max_frm = header[0:4]
                min_frm = self._bytes_to_int(struct.unpack('3B', min_frm))
                max_frm = self._bytes_to_int(struct.unpack('3B', max_frm))
                sample_rate = self._bytes_to_int(header[4:7]) >> 4
                channels = ((header[7] >> 1) & 7) + 1
                bit_depth = ((header[7] & 1) << 4) + ((header[8] & 0xF0) >> 4)
                bit_depth = (bit_depth + 1)
                total_sample_bytes = [(header[8] >> 4)] + list(header[9:12])
                total_samples = self._bytes_to_int(total_sample_bytes)
                md5 = header[12:]
                self.length = float(total_samples) / sample_rate
                return
            else:
                fh.seek(size, 1)
                header_data = fh.read(4)

    def _bytes_to_int(self, b):
        result = 0
        for byte in b:
            result = (result << 8) + byte
        return result

    def _parse_tag(self, fh):
        # for spec, see https://xiph.org/flac/ogg_mapping.html
        header_data = fh.read(4)
        while len(header_data):
            meta_header = struct.unpack('B3B', header_data)
            size = self._bytes_to_int(meta_header[1:4])
            if meta_header[0] == 4:
                oggtag = Ogg(fh, False, False)
                oggtag._parse_vorbis_comment(fh)
                self.update(oggtag)
                return
            else:
                fh.seek(size, 1)
                header_data = fh.read(4)
