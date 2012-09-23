# This file is part of audioread.
# Copyright 2012, Adrian Sampson.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Read audio data using the ffmpeg command line tools via a UNIX
pipe.
"""
import subprocess
import re
import threading
import select
import time

class FFmpegError(Exception):
    pass

class CommunicationError(FFmpegError):
    """Raised when the output of FFmpeg is not parseable."""

class UnsupportedError(FFmpegError):
    """The file could not be decoded by FFmpeg."""

class NotInstalledError(FFmpegError):
    """Could not find the ffmpeg binary."""

class ReadTimeoutError(FFmpegError):
    """Reading from the ffmpeg command-line tool timed out."""

class ReaderThread(threading.Thread):
    """A thread that consumes data from a filehandle. This is used to ensure
    that a buffer for an input stream never fills up.
    """
    # It may seem a little hacky, but this is the most straightforward &
    # reliable way I can think of to do this. select() is sort of
    # inefficient because it doesn't indicate how much is available to
    # read -- so I end up reading character by character.
    def __init__(self, fh, blocksize=1024):
        super(ReaderThread, self).__init__()
        self.fh = fh
        self.blocksize = blocksize
        self.daemon = True
        self.data = []

    def run(self):
        while True:
            data = self.fh.read(self.blocksize)
            if not data:
                break
            self.data.append(data)

class FFmpegAudioFile(object):
    """An audio file decoded by the ffmpeg command-line utility."""
    def __init__(self, filename):
        try:
            self.proc = subprocess.Popen(
                ['ffmpeg', '-i', filename, '-f', 's16le', '-'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except OSError:
            raise NotInstalledError()

        # Read relevant information from stderr.
        self._get_info()

        # Start a separate thread to read the rest of the data from
        # stderr.
        self.stderr_reader = ReaderThread(self.proc.stderr)
        self.stderr_reader.start()

    def read_data(self, block_size=4096, timeout=10.0):
        """Read blocks of raw PCM data from the file."""
        # Read from stdout on this thread.
        start_time = time.time()
        while True:
            # Wait for data to be available or a timeout.
            rready, _, xready = select.select((self.proc.stdout,),
                                              (), (self.proc.stdout,),
                                              timeout)
            end_time = time.time()
            if not rready and not xready:
                if end_time - start_time >= timeout:
                    # Nothing interesting has happened for a while --
                    # FFmpeg is probably hanging.
                    raise ReadTimeoutError(
                        'ffmpeg output: %s' %
                        ''.join(self.stderr_reader.data)
                    )
                else:
                    # Keep waiting.
                    continue
            start_time = end_time

            data = self.proc.stdout.read(block_size)
            if not data:
                break
            yield data

    def _get_info(self):
        """Reads the tool's output from its stderr stream, extracts the
        relevant information, and parses it.
        """
        out_parts = []
        while True:
            line = self.proc.stderr.readline()
            if not line:
                # EOF and data not found.
                raise CommunicationError("stream info not found")
            line = line.strip().lower()

            if b'no such file' in line:
                raise IOError('file not found')
            elif b'invalid data found' in line:
                raise UnsupportedError()
            elif b'duration:' in line:
                out_parts.append(line)
            elif b'audio:' in line:
                out_parts.append(line)
                self._parse_info(b''.join(out_parts))
                break

    def _parse_info(self, s):
        """Given relevant data from the ffmpeg output, set audio
        parameter fields on this object.
        """
        s = str(s)
        # Sample rate.
        match = re.search(r'(\d+) hz', s)
        if match:
            self.samplerate = int(match.group(1))
        else:
            self.samplerate = 0

        # Channel count.
        match = re.search(r'hz, ([^,]+),', s)
        if match:
            mode = match.group(1)
            if mode == 'stereo':
                self.channels = 2
            else:
                match = re.match(r'(\d+) ', mode)
                if match:
                    self.channels = int(match.group(1))
                else:
                    self.channels = 1
        else:
            self.channels = 0

        # Duration.
        match = re.search(
            r'duration: (\d+):(\d+):(\d+).(\d)', s
        )
        if match:
            durparts = list(map(int, match.groups()))
            duration = durparts[0] * 60 * 60 + \
                       durparts[1] * 60 + \
                       durparts[2] + \
                       float(durparts[3]) / 10
            self.duration = duration
        else:
            # No duration found.
            self.duration = 0

    def close(self):
        """Close the ffmpeg process used to perform the decoding."""
        if hasattr(self, 'proc') and self.proc.returncode is None:
            self.proc.terminate()
            # Flush the stdout buffer (stderr already flushed).
            stdout_reader = ReaderThread(self.proc.stdout)
            stdout_reader.start()
            self.proc.wait()

    def __del__(self):
        self.close()

    # Iteration.
    def __iter__(self):
        return self.read_data()

    # Context manager.
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

