CherryMusic is a music streaming server written in python. It's based on cherrypy and jPlayer.

You can search your collection, create and share playlists with other users.

It's able to play music on almost all devices since it happens in your browser and uses HTML5 for audio playback.

Required Dependencies
---------------------

    Python (>= 2.6, >=3.2 preferred),

    CherryPy (>= 3).

If possible, you should install these via your system's package management (on UNIX-like OS).

If you do not want to install CherryPy on your system, you can also use a local copy in your CherryMusic directory instead: When CherryMusic does not find CherryPy on startup, it will offer to download a copy of it into its own directory, keeping your system clean.
Optional Dependencies

Optional dependencies are
--------------------------

- Live transcoding: lame, vorbis-tools, flac, faad2, mpg123 or ffmpeg (which replaces the abovementioned codecs plus adds WMA decoding)

- ID3-Tag reading: stagger (works only with Python 3)

- Automatic resizing of displayed cover art: imagemagick

- For special character search terms: python-unidecode

- For the GTK system tray icon: python-gobject

- HTTPS support in Python 2: pyOpenSSL (in Python 3 it works out of the box)

If possible, you should install those dependencies via your system's package management (on UNIX-like OS).

If you do not want to install stagger on your system, you can simply skip it. On the first start of CherryMusic, it will figure out that stagger is missing and offer you to download a local copy into the CherryMusic directory, keeping your system clean.

Configuration
-------------

Setup in Browser
================

To just get it up and running with a basic setup, issue::

    $ python cherrymusic --setup --port 8080

and open the address "localhost:8080" in your browser (e.g. with Firefox)::

    $ firefox localhost:8080

This will let you configure the most important options from within the browser, after which you can set up the admin account.

Manual setup
============

Start CherryMusic for the initial setup::

    $ python cherrymusic

On first startup CherryMusic will create its data and configuration files in *~/.local/share/cherrymusic/* and *~/.config/cherrymusic/*, print a note to stdout and exit. Now, edit the configuration file in *~/.config/cherrymusic/cherrymusic.conf* and change the following lines to match your setup:

File: *~/.config/cherrymusic/cherrymusic.conf*
::

   [...]

   basedir = /path/to/your/music

   [...]

   port = 8080

   [...]

Open the address "localhost:8080" in your browser (e.g. with `Firefox <https://mozilla.org/firefox>`_) to create an admin account::

   $ firefox localhost:8080

After logging in, populate the search database by clicking *Update Music Library* in the *Admin* panel.

Fine tuning
===========

The configuration of CherryMusic is done in the file *~/.config/cherrymusic/cherrymusic.conf*. The comments in this file should explain all options. If you need further explanations, read the man pages. CherryMusic comes with well-documented manpages. See
::

    $ man cherrymusic

    $ man cherrymusic.conf

for all available options.

Wiki
----
The complete Setup guide can be found `HERE <https://github.com/devsnd/cherrymusic/wiki/Setup-guide>`_
