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
  
You can find more information on the [CherryMusic website](http://www.fomori.org/cherrymusic)
and in our [wiki](https://github.com/devsnd/cherrymusic/wiki).

master: [![Build Status Master](https://travis-ci.org/devsnd/cherrymusic.png?branch=master)](https://travis-ci.org/devsnd/cherrymusic)

devel: [![Build Status Devel](https://travis-ci.org/devsnd/cherrymusic.png?branch=devel)](https://travis-ci.org/devsnd/cherrymusic)


 


Getting Started
---------------

See the [Setup Guide](https://github.com/devsnd/cherrymusic/wiki/Setup-Guide) for quickstart instructions and more.

Basically, you can just 

    $ git clone git://github.com/devsnd/cherrymusic.git

and then start the server and follow the instructions:

    $ python cherrymusic --setup --port 8080
    
(Leave out the --options for subsequent starts.)


Requirements
------------
* [Python](http://python.org/download/releases/) >= 2.6, >= 3.2 preferred
* [CherryPy](http://www.cherrypy.org) >= 3


More
----

See our [wiki](https://github.com/devsnd/cherrymusic/wiki) for user and developer information.


Troubleshooting
---------------

Please see the [Troubleshooting wiki page](https://github.com/devsnd/cherrymusic/wiki/Setup-Guide#wiki-troubleshooting).


Contribute
----------

There's also a wiki section listing the 
[101 ways to lend a hand](https://github.com/devsnd/cherrymusic/wiki/Contribute).

