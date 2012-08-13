cherrymusic
===========

cherrymusic is a standalone music server based on CherryPy and jPlayer. It is intended to be an alternative to edna

Current Features:

  - Browsing and Stream to your music inside the browser (locally or remote)
  - Searching your music
  - Completely AJAX based (no page reloads on click, super fast)
  - Creating playlists
  - Basic Authentification for multiple users
    
Upcoming features:

  - saving and  sharing playlists
  - searching ID3 tags

Getting Started
===============

1. Checkout or download the cherry music sources

2. cp the "config.sample" to "config" and modify to your wishes.

    cp config.sample config
    vi config

3. To use cherrymusic you need to have CherryPy installed. Either you install it using your favorite package-manager or you just download it straight from their website http://download.cherrypy.org/cherrypy/3.2.2/
You can either install it, or just extract the "cherrypy" subfolder inside the cherrymusic folder you just retrieved. That's it. Now simply start the main script using python, it will prompt you for anything else.


    python cherrymusic.py


Side Notes
==========

By default it uses HTML5 for music playback and supports flash as fallback. 

