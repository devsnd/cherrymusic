#!/usr/bin/python3
# -*- Mode: python -*-
#
# $Id: mp3info.py,v 1.2 2006/01/20 03:38:58 timbl Exp $
# 
# Copyright (c) 2002-2004 Vivake Gupta (vivakeATlab49.com).  All rights reserved.
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# This software is maintained by Vivake (vivakeATlab49.com) and is available at:
#     http://www.lab49.com/~vivake/python/MP3Info.py
#
#      ( 7/2003) - Incorporated various changes from Stan Seibert 
#                  <volsungATxiph.org> for more robust ID3 detection.  Includes 
#                  looking for all 11 sync bits and limits on how far to look
#                  for sync bits depending on presence of ID3v2 headers.
#      (11/2003) - Incorporated various changes from Stan Seibert 
#                  <volsungATxiph.org> for must robust ID3 detection.  Includes
#                  fixes to VBR detection and better finding of frame headers.
# 1.2  ( 4/2004) - Integrated a fix from Peter Finlayson <frnknstnATiafrica.com>
#                  for the function ID3v2Frame.  I was determining the size of 
#                  the frame using struct unpacking for signed 8-bit integers,
#                  but should have been getting unsigned 8-bit integers.
# 1.3  ( 4/2004) - Added a proper CVS Id comment.
# 1.4  ( 4/2004) - Added an 'is_vbr' flag to denote that a bitrate from a 
#                  VBR-encoded file is an approximate (average) bitrate.  
#                  Suggested by Willem Broekema <willemATpastelhorn.com>
# 1.5  ( 5/2004) - Protected contributor e-mail addresses from spamming.
# 1.6  ( 5/2004) - Changed 'False' to '0' and 'True' to '1' globally, to work 
#                  with older versions of Python. 
# 1.7  ( 5/2004) - Fixed a mistake in the main call to _parse_xing() where the 
#                  values for seekstart and seeklimit are inverted.  This causes
#                  MP3Info to rarely find the Xing header and report invalid 
#                  lengths for VBR mp3s. Thanks to Christophe Pelte 
#                  <cpelteATnoos.fr> for this patch.
# 1.8  ( 5/2004) - Backported the 'filesize2' attribute from edna, which shows
#                  the filesize in megabytes.
# 1.9  ( 5/2004) - Increased amount of information printed out from command-line
#                  use.
# 1.10 ( 5/2004) - Added the 'length_minutes' and 'length_seconds' attributes,
#                  which are used by edna.  Whoever added them to edna had done
#                  so incorrectly.
# 1.11 ( 5/2004) - Added the 'total_time' attribute, which is just a synonym for
#                  'length,' since it was used by edna.  This allows the current
#                  MP3Info.py to be a drop-in replacement for the old one in
#                  edna.
# 1.12 ( 5/2004) - The program MP3Ext inserts illegal frames, which cause MP3Info
#                  to break.  These are now ignored.  Thanks to Thomas Rowe
#                  <thomas_roweATpsuaslum.com> for reporting this bug.
# 1.2  ( 9/2015) - Ported to python3.


import struct
import string
import random
import re

def _from_synch_safe(synchsafe):
    if isinstance(synchsafe, type(1)):
        (b3, b2, b1, b0) = struct.unpack('!4b', struct.pack('!1i', synchsafe))
    else:
        while len(synchsafe) < 4:
            synchsafe = (0,) + synchsafe
        (b3, b2, b1, b0) = synchsafe

    x = 128
    return (((b3 * x + b2) * x + b1) * x + b0)

def _strip_zero(s):
    start = 0
    while start < len(s) and (s[start] == '\0' or s[start] == ' '):
        start = start + 1

    end = len(s) - 1
    while end >= 0 and (s[end] == '\0' or s[end] == ' '):
        end = end - 1

    return s[start:end+1]

class Error(Exception):
    pass

# MP3ext causes illegal frames to be inserted, which must be ignored.
_known_bad_frames = [
    "\x00\x00MP",
    "\x00MP3",
    " MP3",
    "MP3e",
    "\x00MP",
    " MP",
    "MP3",
]

class ID3v2Frame:
    def __init__(self, file, version):
        self.name = ""
        self.version = 0
        self.padding = 0
        self.size = 0
        self.data = ""

        self.flags = {}
        self.f_tag_alter_preservation = 0
        self.f_file_alter_preservation = 0
        self.f_read_only = 0
        self.f_compression = 0
        self.f_encryption = 0
        self.f_grouping_identity = 0
        self.f_unsynchronization = 0
        self.f_data_length_indicator = 0

        if version == 2:
            nameSize = 3
        else:
            nameSize = 4
        self.name = file.read(nameSize)

        # mp3ext writes padding (wrongfully) as "MP3ext V...."
        # so we ignore this tag.
        if self.name in _known_bad_frames:
            self.padding = 1
            return

        self.version = version

        if self.name == nameSize * '\0':
            self.padding = 1
            return

        if self.name[0] < 'A' or self.name[0] > 'Z':
            self.padding = 1
            return

        size = ()
        if version == 2:
            size = struct.unpack('!3B', file.read(3))
            self.size = (size[0] * 256 + size[1]) * 256 + size[2]
        elif version == 3:
            size = struct.unpack('!L', file.read(4))
            self.size = size[0]
        elif version == 4:
            size = struct.unpack('!4B', file.read(4))
            self.size = _from_synch_safe(size)

        if version == 3:  # abc00000 def00000
            (flags,) = struct.unpack('!1b', file.read(1))
            self.f_tag_alter_preservation  = flags >> 7 & 1 #a
            self.f_file_alter_preservation = flags >> 6 & 1 #b
            self.f_read_only               = flags >> 5 & 1 #c
            (flags,) = struct.unpack('!1b', file.read(1))
            self.f_compression             = flags >> 7 & 1 #d
            self.f_encryption              = flags >> 6 & 1 #e
            self.f_grouping_identity       = flags >> 5 & 1 #f
        elif version == 4: # 0abc0000 0h00kmnp
            (flags,) = struct.unpack('!1b', file.read(1))
            self.f_tag_alter_preservation  = flags >> 6 & 1 #a
            self.f_file_alter_preservation = flags >> 5 & 1 #b
            self.f_read_only               = flags >> 4 & 1 #c
            (flags,) = struct.unpack('!1b', file.read(1))
            self.f_grouping_identity       = flags >> 6 & 1 #h
            self.f_compression             = flags >> 3 & 1 #k
            self.f_encryption              = flags >> 2 & 1 #m
            self.f_unsynchronization       = flags >> 1 & 1 #n
            self.f_data_length_indicator   = flags >> 0 & 1 #p

        self.data = _strip_zero(file.read(self.size))

_genres = [
    "Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk", "Grunge",
    "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other", "Pop", "R&B",
    "Rap", "Reggae", "Rock", "Techno", "Industrial", "Alternative", "Ska",
    "Death Metal", "Pranks", "Soundtrack", "Euro-Techno", "Ambient", "Trip-Hop",
    "Vocal", "Jazz+Funk", "Fusion", "Trance", "Classical", "Instrumental",
    "Acid", "House", "Game", "Sound Clip", "Gospel", "Noise", "AlternRock",
    "Bass", "Soul", "Punk", "Space", "Meditative", "Instrumental Pop",
    "Instrumental Rock", "Ethnic", "Gothic", "Darkwave", "Techno-industrial",
    "Electronic", "Pop-Folk", "Eurodance", "Dream", "Southern Rock", "Comedy",
    "Cult", "Gangsta", "Top 40", "Christian Rap", "Pop/Funk", "Jungle",
    "Native American", "Cabaret", "New Wave", "Psychadelic", "Rave",
    "Showtunes", "Trailer", "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz",
    "Polka", "Retro", "Musical", "Rock & Roll", "Hard Rock", "Folk",
    "Folk/Rock", "National Folk", "Swing", "Fast-Fusion", "Bebob", "Latin",
    "Revival", "Celtic", "Bluegrass", "Avantegarde", "Gothic Rock",
    "Progressive Rock", "Psychedelic Rock", "Symphonic Rock", "Slow Rock",
    "Big Band", "Chorus", "Easy Listening", "Acoustic", "Humour", "Speech",
    "Chanson", "Opera", "Chamber Music", "Sonata", "Symphony", "Booty Bass",
    "Primus", "Porn Groove", "Satire", "Slow Jam", "Club", "Tango", "Samba",
    "Folklore", "Ballad", "Power Ballad", "Rythmic Soul", "Freestyle", "Duet",
    "Punk Rock", "Drum Solo", "A capella", "Euro-House", "Dance Hall", "Goa",
    "Drum & Bass", "Club House", "Hardcore", "Terror", "Indie", "BritPop",
    "NegerPunk", "Polsk Punk", "Beat", "Christian Gangsta", "Heavy Metal",
    "Black Metal", "Crossover", "Contemporary Christian", "Christian Rock", "Merengue",
    "Salsa", "Thrash Metal", "Anime", "JPop", "SynthPop",
]

class ID3v1:
    def __init__(self, file):
        self.valid = 0

        self.tags = { }

        try:
            file.seek(-128, 2)
        except IOError:
            pass

        data = file.read(128)
        if data[0:3] != 'TAG':
            return
        else:
            self.valid = 1

        self.tags['TT2'] = _strip_zero(data[ 3: 33])
        self.tags['TP1'] = _strip_zero(data[33: 63])
        self.tags['TAL'] = _strip_zero(data[63: 93])
        self.tags['TYE'] = _strip_zero(data[93: 97])
        self.tags['COM'] = _strip_zero(data[97:125])

        if data[125] == '\0':
            self.tags['TRK'] = ord(data[126])

        try:
            self.tags['TCO'] = _genres[ord(data[127])]
        except IndexError:
            self.tags['TCO'] = None
        

class ID3v2:
    def __init__(self, file):
        self.valid = 0

        self.tags = { }

        self.header_size = 0

        self.major_version = 0
        self.minor_version = 0

        self.f_unsynchronization = 0
        self.f_extended_header = 0
        self.f_experimental = 0
        self.f_footer = 0

        self.f_extended_header_zie = 0
        self.f_extended_num_flag_bytes = 0

        self.ef_update = 0
        self.ef_crc = 0
        self.ef_restrictions = 0

        self.crc = 0
        self.restrictions = 0

        self.frames = []
        self.tags = {}
        
        file.seek(0, 0)
        if file.read(3) != "ID3":
            return
        else:
            self.valid = 1

        (self.major_version, self.minor_version) = struct.unpack('!2b', file.read(2))

        # abcd 0000
        (flags,) = struct.unpack('!1b', file.read(1))
        self.f_unsynchronization = flags >> 7 & 1 # a
        self.f_extended_header   = flags >> 6 & 1 # b
        self.f_experimental      = flags >> 5 & 1 # c
        self.f_footer            = flags >> 4 & 1 # d

        self.header_size = _from_synch_safe(struct.unpack('!4b', file.read(4)))

        while 1:
            if file.tell() >= self.header_size:
                break
            frame = ID3v2Frame(file, self.major_version)
            if frame.padding:
                file.seek(self.header_size)
                break

            self.frames = self.frames + [frame]
            self.tags[frame.name] = frame.data

_bitrates = [
    [ # MPEG-2 & 2.5
        [0,32,48,56, 64, 80, 96,112,128,144,160,176,192,224,256,None], # Layer 1
        [0, 8,16,24, 32, 40, 48, 56, 64, 80, 96,112,128,144,160,None], # Layer 2
        [0, 8,16,24, 32, 40, 48, 56, 64, 80, 96,112,128,144,160,None]  # Layer 3
    ],

    [ # MPEG-1
        [0,32,64,96,128,160,192,224,256,288,320,352,384,416,448,None], # Layer 1
        [0,32,48,56, 64, 80, 96,112,128,160,192,224,256,320,384,None], # Layer 2
        [0,32,40,48, 56, 64, 80, 96,112,128,160,192,224,256,320,None]  # Layer 3
    ]
]

_samplerates = [
    [ 11025, 12000,  8000, None], # MPEG-2.5
    [  None,  None,  None, None], # reserved
    [ 22050, 24000, 16000, None], # MPEG-2
    [ 44100, 48000, 32000, None], # MPEG-1
]                                                                                                               
                                                                                                                  
_modes = [ "stereo", "joint stereo", "dual channel", "mono" ]

_mode_extensions = [
    [ "4-31", "8-31", "12-31", "16-31" ],
    [ "4-31", "8-31", "12-31", "16-31" ],
    [     "",   "IS",    "MS", "IS+MS" ]
]

_emphases = [ "none", "50/15 ms", "reserved", "CCIT J.17" ]

_MP3_HEADER_SEEK_LIMIT = 500000

class MPEG:
    def __init__(self, file, seeklimit=_MP3_HEADER_SEEK_LIMIT, seekstart=0):
        self.valid = 0

        file.seek(0, 2)
        self.filesize = file.tell()
        self.filesize2 = round(float(self.filesize/1024/1024), 2)

        self.version = 0
        self.layer = 0
        self.protection = 0
        self.bitrate = 0
        self.is_vbr = 0
        self.samplerate = 0
        self.padding = 0
        self.private = 0
        self.mode = ""
        self.mode_extension = ""
        self.copyright = 0
        self.original = 0
        self.emphasis = ""
        self.length = 0
        self.length_minutes = 0
        self.length_seconds = 0
        self.total_time = 0 # added for easy incorporation into edna

        # The longest possible frame for any MPEG audio file
        # is 4609 bytes for a MPEG 2, Layer 1 256 kbps, 8000Hz with
        # a padding slot.  Add an extra 4 bytes to ensure we get the
        # next header and round up to a multiple of 4 to get the magic
        # number 4616.  If this is an MPEG file, then from a random
        # point in the middle (far away from the tag stupidity), we
        # should always find an MPEG frame header in any 4616 byte
        # substring.
        #
        # We pick a location in the middle 50% of the file to
        # do a header test, and we require that we find three consecutive
        # frame headers in a row, as calculated by their frame lengths.
        # If it passes, then we proceed with parsing (using much less
        # restrictive searching)
        test_pos = int(random.uniform(0.25,0.75) * self.filesize)

        offset, header = self._find_header(file, seeklimit=4616,
                                           seekstart=test_pos,
                                           check_next_header=2)
        if offset == -1 or header is None:
            raise Error("Failed MPEG frame test.")
            
        # Now we can look for the first header
        offset, header = self._find_header(file, seeklimit, seekstart)
        if offset == -1 or header is None:
            raise Error("Could not find MPEG header")

        # Note that _find_header already parsed the header
        
        if not self.valid:
            raise Error("MPEG header not valid")

        self._parse_xing(file, seekstart, seeklimit)

        self.length_minutes = int(self.length / 60)
        self.length_seconds = int(round(self.length % 60))
        self.total_time = self.length # added for easy incorporation into edna

    def _find_header(self, file, seeklimit=_MP3_HEADER_SEEK_LIMIT,
                     seekstart=0, check_next_header=1):
        amt = 5120  # Multiple of 512 is hopefully more efficient to read from
                    # disk, and size ensure the random test will only
                    # read once
        curr_pos = 0
        read_more = 0 # False

#        print("_find_header(", seeklimit, seekstart, check_next_header, ")")

        file.seek(int(seekstart), 0)
        # Don't read more than we are allowed to see (size of header is 4)
        header = file.read(min(amt,seeklimit+4))
        
        while curr_pos <= seeklimit:            
            # look for the sync byte
#            offset = string.find(header, chr(255), curr_pos)
            offset = -1
            i = curr_pos
            while i < len(header):
                if header[i] == 255:
                    offset = i
                    i = len(header)
                else:
                    i = i+1 

#            print(curr_pos, seekstart)

            if offset == -1:
                curr_pos = len(header)  # Header after everything so far
                read_more = 1 # True
            elif offset + 4 > len(header):
                curr_pos = offset  # Need to read more, jump back here later
                read_more = 1 # True
            elif header[offset+1] & 0xE0 == 0xE0:

                # Finish now if we should not check the next header
                if check_next_header == 0:
                    return seekstart+offset, header[offset:offset+4]

                # We have a possible winner, test parse this header and
                # check if the next header is in the right place.
                # WARNING: _parse_header has side effects!  This should
                # be fixed, though in this case it does not matter.
                self._parse_header(header[offset:offset+4])
                    
                if self.valid:

                    file_pos = file.tell()
                    
                    next_off, next_header = \
                              self._find_header(file, seeklimit=0,
                                        seekstart=int(seekstart+offset
                                                  +self.framelength),
                                        check_next_header=check_next_header-1)

                    # Move the file pointer back
                    file.seek(file_pos,0)
                    
                    if next_off != -1:
                        return seekstart+offset, header[offset:offset+4]
                    else:
                        curr_pos = offset+2
                else:
                    curr_pos = offset+2
                    
            else:
                curr_pos = offset+2 # Gotta be after the 2 bytes we looked at

            if read_more and curr_pos <= seeklimit:
                chunk = file.read(amt)
                if len(chunk) == 0:
                    # no more to read, give up
                    return -1, None
                else:
                    header += chunk
        
        # couldn't find the header
        return -1, None

    def _parse_header(self, header):
        self.valid = 0 # Assume the worst until proven otherwise
        
        # AAAAAAAA AAABBCCD EEEEFFGH IIJJKLMM
        (bytes,) = struct.unpack('>i', header)
        mpeg_version =    (bytes >> 19) & 3  # BB   00 = MPEG2.5, 01 = res, 10 = MPEG2, 11 = MPEG1  
        layer =           (bytes >> 17) & 3  # CC   00 = res, 01 = Layer 3, 10 = Layer 2, 11 = Layer 1
        protection_bit =  (bytes >> 16) & 1  # D    0 = protected, 1 = not protected
        bitrate =         (bytes >> 12) & 15 # EEEE 0000 = free, 1111 = bad
        samplerate =      (bytes >> 10) & 3  # F    11 = res
        padding_bit =     (bytes >> 9)  & 1  # G    0 = not padded, 1 = padded
        private_bit =     (bytes >> 8)  & 1  # H
        mode =            (bytes >> 6)  & 3  # II   00 = stereo, 01 = joint stereo, 10 = dual channel, 11 = mono
        mode_extension =  (bytes >> 4)  & 3  # JJ
        copyright =       (bytes >> 3)  & 1  # K    00 = not copyrighted, 01 = copyrighted                            
        original =        (bytes >> 2)  & 1  # L    00 = copy, 01 = original                                          
        emphasis =        (bytes >> 0)  & 3  # MM   00 = none, 01 = 50/15 ms, 10 = res, 11 = CCIT J.17                

        if mpeg_version == 0:
            self.version = 2.5
        elif mpeg_version == 2:
            self.version = 2
        elif mpeg_version == 3:
            self.version = 1
        else:
            return

        if layer > 0:
            self.layer = 4 - layer
        else:
            return

        self.protection = protection_bit

        self.bitrate = _bitrates[mpeg_version & 1][self.layer - 1][bitrate]
        self.samplerate = _samplerates[mpeg_version][samplerate]
        
        if self.bitrate is None or self.samplerate is None:
            return

        self.padding = padding_bit
        self.private = private_bit
        self.mode = _modes[mode]
        self.mode_extension = _mode_extensions[self.layer - 1][mode_extension]
        self.copyright = copyright
        self.original = original
        self.emphasis = _emphases[emphasis]
        try:
            if self.layer == 1:
                self.framelength = (12000 * self.bitrate / self.samplerate + padding_bit) * 4
                self.samplesperframe = 384.0
            elif self.layer == 2:
                self.framelength =  144000 * self.bitrate / self.samplerate + padding_bit
                self.samplesperframe = 1152.0
            else:
                # MPEG 2 and 2.5 calculate framelength different
                # (discovered in LAME source)
                if mpeg_version == 0 or mpeg_version == 2:
                    fake_samplerate = self.samplerate << 1
                else:
                    fake_samplerate = self.samplerate
                    
                self.framelength = 144000 * self.bitrate / fake_samplerate + padding_bit
                self.samplesperframe = 1152.0 # This might be wrong
                

#            print("framelength ", self.framelength)
#            print("bitrate ",self.bitrate)
#            print("samplerate ",self.samplerate)
#            print("samplesperframe ",self.samplesperframe)


#            self.length = int(round((self.filesize / self.framelength) * (self.samplesperframe / self.samplerate)))
            self.length = int((self.filesize / (self.bitrate * 1000.0)*8))
        except ZeroDivisionError:
            return  # Division by zero means the header is bad

        # More sanity checks
        if self.framelength < 0 or self.length < 0:
            return
        
        self.valid = 1

    def _parse_xing(self, file, seekstart=0, seeklimit=_MP3_HEADER_SEEK_LIMIT):
        """Parse the Xing-specific header.

        For variable-bitrate (VBR) MPEG files, Xing includes a header which
        can be used to approximate the (average) bitrate and the duration
        of the file.
        """

        return

        file.seek(seekstart, 0)
        header = file.read(seeklimit)

        try:
            i = string.find(header, 'Xing')
            if i > 0:
                header += file.read(128)
                (flags,) = struct.unpack('>i', header[i+4:i+8])
                if flags & 3:
                    # flags says "frames" and "bytes" are present. use them.
                    (frames,) = struct.unpack('>i', header[i+8:i+12])
                    (bytes,) = struct.unpack('>i', header[i+12:i+16])

                    if self.samplerate:
                        length = int(round(frames * self.samplesperframe / self.samplerate))
                        bitrate = ((bytes * 8.0 / length) / 1000)
                        self.length = length
                        self.bitrate = bitrate
                        self.is_vbr = 1
                        return
        except ZeroDivisionError:
            pass # This header is bad
        except struct.error:
            pass # This header is bad

        # If we made it here, the header wasn't any good.  Try at the beginning
        # now just in case
        if seekstart != 0:
            self._parse_xing(file, 0, seeklimit)
        
class MP3Info:

    num_regex = re.compile("\d+")
    
    def __init__(self, file):
        self.valid = 0

        self.id3 = None
        self.mpeg = None

        # No sense in making clients guess whether these variables exists
        self.title = self.artist = self.track = self.year = \
                     self.comment = self.composer = self.album = \
                     self.disc = self.genre = self.encoder = None

        id3 = ID3v1(file)
        if id3.valid:
            self.id3 = id3

        id3v2 = ID3v2(file)
        if id3v2.valid and id3v2.tags != {}:
            self.id3 = id3v2

        if id3v2.valid:
            # ID3v2 size (header_size) doesn't include 10 bytes of header
            self.mpeg = MPEG(file, seekstart=id3v2.header_size+10)
        else:
            # Header better be near the beginning if there is no ID3v2
            self.mpeg = MPEG(file)


        if self.id3 is None:
            return
        
        for tag in self.id3.tags.keys():
            if tag == 'TT2' or tag == 'TIT2':
                self.title = self.id3.tags[tag]
            elif tag == 'TP1' or tag == 'TPE1':
                self.artist = self.id3.tags[tag]
            elif tag == 'TRK' or tag == 'TRCK':
                self.track = self.id3.tags[tag]
            elif tag == 'TYE' or tag == 'TYER':
                self.year = self.id3.tags[tag]
            elif tag == 'COM' or tag == 'COMM':
                self.comment = self.id3.tags[tag]
            elif tag == 'TCM':
                self.composer = self.id3.tags[tag]
            elif tag == 'TAL' or tag == 'TALB':
                self.album = self.id3.tags[tag]
            elif tag == 'TPA':
                self.disc = self.id3.tags[tag]
            elif tag == 'TCO' or tag == 'TCON':
                self.genre = self.id3.tags[tag]
                if self.genre and self.genre[0] == '(' and self.genre[-1] == ')':
                    genres = self.num_regex.findall(self.genre)
                    if len(genres) > 0:
                        try:
                            # Force to single valued even if multiple
                            self.genre = _genres[int(genres[0])]
                        except IndexError:
                            self.genre = ""
                    else:
                        self.genre = ""
            elif tag == 'TEN' or tag == 'TENC':
                self.encoder = self.id3.tags[tag]

if __name__ == '__main__':
    import sys
    i = MP3Info(open(sys.argv[1], 'rb'))
    print("File Info")
    print("---------")
    for key in i.__dict__.keys():
        print(key, ": ", i.__dict__[key])

    print
    print("MPEG Info")
    print("---------")
    for key in i.mpeg.__dict__.keys():
        print(key, ": ", i.mpeg.__dict__[key])

    print
    if not i.id3 is None:
        print("ID3 Info")
        print("--------")
        for key in i.id3.__dict__.keys():
            print(key, ": ", i.id3.__dict__[key])
        print
