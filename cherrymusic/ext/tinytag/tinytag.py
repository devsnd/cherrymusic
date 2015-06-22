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


class TinyTag(object):
    """Base class for all tag types"""
    def __init__(self, filehandler, filesize):
        self._filehandler = filehandler
        self.filesize = filesize
        self.track = None
        self.track_total = None
        self.title = None
        self.artist = None
        self.album = None
        self.year = None
        self.genre = None
        self.duration = 0
        self.audio_offset = 0
        self.bitrate = 0.0  # must be float for later VBR calculations
        self.samplerate = 0
        self._load_image = False
        self._image_data = None

    def get_image(self):
        return self._image_data

    def has_all_tags(self):
        """check if all tags are already defined. Useful for ID3 tags
        since multiple kinds of tags can be in one audio file
        """
        return all((self.track, self.track_total, self.title,
                    self.artist, self.album, self.year, self.genre))

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
                ('.oga', '.ogg'): Ogg,
                ('.wav'): Wave,
                ('.flac'): Flac,
                ('.wma'): Wma,
            }
            for fileextension, tagclass in mapping.items():
                if filename.lower().endswith(fileextension):
                    parser_class = tagclass
        else:
            # use class on which the method was invoked as parser
            parser_class = cls
        if parser_class is None:
            raise LookupError('No tag reader found to support filetype! ')
        with open(filename, 'rb') as af:
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
            self._filehandler.seek(0)
        if duration:
            self._determine_duration(self._filehandler)

    def _set_field(self, fieldname, bytestring, transfunc=None):
        """convienience function to set fields of the tinytag by name.
        the payload (bytestring) can be changed using the transfunc"""
        if getattr(self, fieldname):
            return
        if transfunc:
            setattr(self, fieldname, transfunc(bytestring))
        else:
            setattr(self, fieldname, bytestring)

    def _determine_duration(self, fh):
        raise NotImplementedError()

    def _parse_tag(self, fh):
        raise NotImplementedError()

    def update(self, other):
        """update the values of this tag with the values from another tag"""
        for key in ['track', 'track_total', 'title', 'artist',
                    'album', 'year', 'duration', 'genre']:
            if not getattr(self, key) and getattr(other, key):
                setattr(self, key, getattr(other, key))

    def _bytes_to_int(self, b):
        result = 0
        for byte in b:
            result = (result << 8) + byte
        return result

    def _bytes_to_int_le(self, b):
        result = 0
        for idx in range(len(b)): # uglyness for py2/3 compat
            result += (struct.unpack('B', b[idx:idx+1])[0] << 8*idx)
        return result

    def _unpad(self, s):
        # strings in mp3 and asf _can_ be terminated with a zero byte at the end
        return s[:s.index('\x00')] if '\x00' in s else s

class ID3(TinyTag):
    FRAME_ID_TO_FIELD = {  # Mapping from Frame ID to a field of the TinyTag
        'TRCK': 'track',  'TRK': 'track',
        'TYER': 'year',   'TYE': 'year',
        'TALB': 'album',  'TAL': 'album',
        'TPE1': 'artist', 'TP1': 'artist',
        'TIT2': 'title',  'TT2': 'title',
        'TCON': 'genre',
    }
    _MAX_ESTIMATION_SEC = 30

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

    ]

    def __init__(self, filehandler, filesize):
        TinyTag.__init__(self, filehandler, filesize)
        # save position after the ID3 tag for duration mesurement speedup
        self._bytepos_after_id3v2 = 0

    @classmethod
    def set_estimation_precision(cls, estimation_in_seconds):
        cls._MAX_ESTIMATION_SEC = estimation_in_seconds

    def _determine_duration(self, fh):
        max_estimation_frames = (ID3._MAX_ESTIMATION_SEC*44100) // 1152
        frame_size_mean = 0
        # set sample rate from first found frame later, default to 44khz
        file_sample_rate = 44100
        # see this page for the magic values used in mp3:
        # http://www.mpgedit.org/mpgedit/mpeg_format/mpeghdr.htm
        bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192,
                    224, 256, 320]
        samplerates = [44100, 48000, 32000]
        header_bytes = 4
        frames = 0  # count frames for determining mp3 duration
        # seek to first position after id3 tag (speedup for large header)
        fh.seek(self._bytepos_after_id3v2)
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
                        # invalid frame! roll back to last position
                        fh.seek(-2, os.SEEK_CUR)
                        continue
                    frames += 1  # it's most probably an mp3 frame
                    bitrate = bitrates[br_id]
                    samplerate = samplerates[sr_id]
                    # running average of bitrate
                    self.bitrate = (self.bitrate*(frames-1) + bitrate)/frames
                    if frames == 1:
                        # we already read the 4 bytes frame header
                        self.audio_offset = fh.tell() - 4
                        self.samplerate = samplerate
                    padding = 1 if bitrate_freq & 0x02 > 0 else 0
                    frame_length = (144000 * bitrate) // samplerate + padding
                    frame_size_mean += frame_length
                    if frames == max_estimation_frames:
                        # try to estimate duration
                        fh.seek(-1, 2)  # jump to last byte
                        estimated_frame_count = fh.tell() / (frame_size_mean / frames)
                        samples = estimated_frame_count * 1152
                        self.duration = samples/float(self.samplerate)
                        return
                    if frame_length > 1:
                        # jump over current frame body
                        fh.seek(frame_length - header_bytes, os.SEEK_CUR)
        samples = frames * 1152  # 1152 is the default frame size for mp3
        if self.samplerate:
            self.duration = samples/float(self.samplerate)

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
            size = self._calc_size(header[4:9], 7)
            self._bytepos_after_id3v2 = size
            parsed_size = 0
            if extended:  # just read over the extended header.
                size_bytes = struct.unpack('4B', fh.read(6)[0:4])
                extd_size = self._calc_size(size_bytes, 7)
                fh.read(extd_size - 6)
            while parsed_size < size:
                is_id3_v22 = major == 2
                frame_size = self._parse_frame(fh, is_v22=is_id3_v22)
                if frame_size == 0:
                    break
                parsed_size += frame_size

    def _parse_id3v1(self, fh):
        if fh.read(3) == b'TAG':  # check if this is an ID3 v1 tag
            asciidecode = lambda x: self._unpad(codecs.decode(x, 'latin1'))
            self._set_field('title', fh.read(30), transfunc=asciidecode)
            self._set_field('artist', fh.read(30), transfunc=asciidecode)
            self._set_field('album', fh.read(30), transfunc=asciidecode)
            self._set_field('year', fh.read(4), transfunc=asciidecode)
            comment = fh.read(30)
            if b'\x00\x00' < comment[-2:] < b'\x01\x00':
                self._set_field('track', str(ord(comment[-1:])))
            genre_id = ord(fh.read(1))
            if genre_id < len(ID3.ID3V1_GENRES):
                self.genre = ID3.ID3V1_GENRES[genre_id]

    def _parse_frame(self, fh, is_v22=False):
        encoding = 'ISO-8859-1'  # default encoding used in most mp3 tags
        # ID3v2.2 especially ugly. see: http://id3.org/id3v2-00
        frame_header_size = 6 if is_v22 else 10
        frame_size_bytes = 3 if is_v22 else 4
        binformat = '3s3B' if is_v22 else '4s4B2B'
        bits_per_byte = 7 if is_v22 else 8
        frame_header_data = fh.read(frame_header_size)
        if len(frame_header_data) == 0:
            return 0
        frame = struct.unpack(binformat, frame_header_data)
        frame_id = self._decode_string(frame[0])

        frame_size = self._calc_size(frame[1:1+frame_size_bytes], bits_per_byte)
        if frame_size > 0:
            # flags = frame[1+frame_size_bytes:] # dont care about flags.
            content = fh.read(frame_size)
            fieldname = ID3.FRAME_ID_TO_FIELD.get(frame_id)
            if fieldname:
                if fieldname == 'track':
                    self._parse_track(content)
                else:
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
        first_byte = b[:1]
        if first_byte == b'\x00':
            return self._unpad(codecs.decode(b[1:], 'ISO-8859-1'))
        elif first_byte == b'\x01':
            # strip the bom and optional null bytes
            bytestr = b[3:-1] if len(b) % 2 == 0 else b[3:]
            return self._unpad(codecs.decode(bytestr, 'UTF-16'))
        elif first_byte == b'\x02':
            # strip optional null byte
            bytestr = b[1:-1] if len(b) % 2 == 0 else b[1:]
            return self._unpad(codecs.decode(bytestr, 'UTF-16be'))
        elif first_byte == b'\x03':
            return codecs.decode(b[1:], 'UTF-8')
        return self._unpad(codecs.decode(b, 'ISO-8859-1'))

    def _parse_track(self, b):
        track = self._decode_string(b)
        track_total = None
        if '/' in track:
            track, track_total = track.split('/')
        self._set_field('track', track)
        self._set_field('track_total', track_total)

    def _calc_size(self, bytestr, bits_per_byte):
        # length of some mp3 header fields is described
        # by "7-bit-bytes" or sometimes 8-bit bytes...
        ret = 0
        for b in bytestr:
            ret <<= bits_per_byte
            ret += b
        return ret


class StringWalker(object):
    """file obj like string. probably there are buildins doing this already"""
    def __init__(self, string):
        self.string = string

    def read(self, nbytes):
        retstring, self.string = self.string[:nbytes], self.string[nbytes:]
        return retstring


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
            b = fh.read(1)
            if len(b) == 0:
                return  # EOF
            if b == b'O':  # look for an ogg header
                if fh.read(3) == b'ggS':
                    fh.seek(-4, 1)  # parse the page header from start
                    for packet in self._parse_pages(fh):
                        pass  # parse all remaining pages
                    self.duration = self._max_samplenum / float(self.samplerate)
                else:
                    fh.seek(-3, 1)  # oops, no header, rewind selectah!

    def _parse_tag(self, fh):
        page_start_pos = fh.tell()  # set audio_offest later if its audio data
        for packet in self._parse_pages(fh):
            walker = StringWalker(packet)
            header = walker.read(7)
            if header == b"\x01vorbis":
                (channels, self.samplerate, max_bitrate, bitrate,
                 min_bitrate) = struct.unpack("<B4i", packet[11:28])
                if not self.audio_offset:
                    self.bitrate = bitrate / 1024
                    self.audio_offset = page_start_pos
            elif header == b"\x03vorbis":
                self._parse_vorbis_comment(walker)
            else:
                break
            page_start_pos = fh.tell()

    def _parse_vorbis_comment(self, fh):
        # for the spec, see: http://xiph.org/vorbis/doc/v-comment.html
        comment_type_to_attr_mapping = {
            'album': 'album',
            'title': 'title',
            'artist': 'artist',
            'date': 'year',
            'tracknumber': 'track',
            'genre': 'genre'
        }
        vendor_length = struct.unpack('I', fh.read(4))[0]
        vendor = fh.read(vendor_length)
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
    def __init__(self, filehandler, filesize):
        TinyTag.__init__(self, filehandler, filesize)
        self._duration_parsed = False

    def _determine_duration(self, fh):
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
                _, channels, self.samplerate = struct.unpack('HHI', fh.read(8))
                _, _, bitdepth = struct.unpack('<IHH', fh.read(8))
                self.bitrate = self.samplerate * channels * bitdepth / 1024
            elif subchunkid == b'data':
                self.duration = subchunksize/channels/samplerate/(bitdepth/8)
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
            return  # not a flac file!
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
        if value_type == 0:
            return self.__decode_string(value)
        elif value_type == 1:
            return value
        elif 1 < value_type < 6:
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
            if object_size == 0:
                break
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
                    'WM/Year': 'year',
                    'WM/AlbumArtist': 'album',
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
                        self._set_field(field_name, str(field_value))
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
                fh.read(blocks['type_specific_data_length'] - already_read)
                fh.read(blocks['error_correction_data_length'])
            else:
                fh.read(object_size - 24) # read over onknown object ids
