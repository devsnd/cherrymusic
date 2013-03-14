CherryMusic
===========

CherryMusic is a music streaming server based on CherryPy and jPlayer.
It plays the music inside your PC, smartphone, tablet, toaster or whatever 
device has a HTML5 compliant browser installed.


current features:

  - stream your music inside the browser (locally or remote)
  - browse and search your music
  - completely AJAX based (no page reloads on click, therefore fast)
  - create and share playlists
  - multiple user authentication
  - HTTPS support
  - automatic album cover art fetching
  - see CHANGES for all the features
  
You can find more information on the [CherryMusic website](http://www.fomori.org/cherrymusic).

master | devel
--- | --- 
[![Build Status](https://travis-ci.org/devsnd/cherrymusic.png?branch=master)](https://travis-ci.org/devsnd/cherrymusic) | [![Build Status](https://travis-ci.org/devsnd/cherrymusic.png?branch=devel)](https://travis-ci.org/devsnd/cherrymusic)
 



Getting Started
---------------

1. [We're on github](https://github.com/devsnd/cherrymusic). Checkout or download the cherrymusic sources, e.g.:

        $ git clone git://github.com/devsnd/cherrymusic.git
    
2. To use cherrymusic you need [CherryPy](http://www.cherrypy.org). There are two options:
    - Install it. Use your favorite package manager,
      or [download](http://download.cherrypy.org/cherrypy/3.2.2/) it and do a manual install.
    - If you only want to test cherrymusic without installing any dependencies, you
      can simply start CherryMusic and it will ask you if you want it to install
      cherrypy in the local folder for you.


3. Now simply run the main script using python

        $ python cherrymusic --setup --port 8080

4. Open your browser configure cherrymusic and play some music!

        $ firefox localhost:8080

Requirements
------------
* [Python](http://python.org/download/releases/)
* [CherryPy](http://www.cherrypy.org)


Optional Dependencies
---------------------
python 2:
  
  - HTTPS support: pyOpenSSL

python 3:

  - ID3 Tag Support: stagger

Known Issues
------------

An active flash blocker can interfere with the web frontend. 
If you have trouble with things like track selection or playback, try whitelisting
the server in your browser's flash blocker / plugin manager.

On Windows:
```
FileNotFoundError: [WinError 2] The system cannot find the file specified: 'C:\\Documents and Settings\\username\\.cherrymusic\
\sessions\\session-622d41384b5f877a840ba5dfe38408dc4853e8f4.lock'
```
This error can be circumvented by setting the

        keep_session_in_ram = True

in the configuration file (`C:\Documents and Settings\username\Application Data\cherrymusic\config`).
