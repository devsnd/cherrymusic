#!/usr/bin/python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import os
import sqlite3

PLAYLISTDBFILE = 'playlist.db'

class PlaylistDB:
    def __init__(self):
        setupDB = not os.path.isfile(PLAYLISTDBFILE) or os.path.getsize(PLAYLISTDBFILE) == 0
        self.conn = sqlite3.connect(PLAYLISTDBFILE, check_same_thread=False)
        if setupDB:
            print('Creating playlist db...')
            self.conn.execute('CREATE TABLE playlists (title text, userid int, public int)')
            self.conn.execute('CREATE TABLE tracks (playlistid int, track int, url text, title text)')
            self.conn.commit()
            print('done.')
            print('Connected to Database. (' + PLAYLISTDBFILE + ')')

    def savePlaylist(self, userid, public, playlist, playlisttitle):
        if not len(playlist):
            print('I will not create an empty playlist. sorry.')
            return
        cursor = self.conn.cursor()
        cursor.execute("""INSERT INTO playlists 
            (title, userid, public) VALUES (?,?,?)""",
            (playlisttitle, userid, 1 if public else 0))
        playlistid = cursor.lastrowid;
        #put tracknumber to each track
        numberedplaylist = []
        for entry in zip(range(len(playlist)), playlist):
            track = entry[0]
            song = entry[1]
            numberedplaylist.append((playlistid, track, song['mp3'], song['title']))
        cursor.executemany("""INSERT INTO tracks (playlistid, track, url, title) 
            VALUES (?,?,?,?)""", numberedplaylist)
        self.conn.commit()


    def loadPlaylist(self, playlistid, userid):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT rowid FROM playlists WHERE 
            rowid = ? AND (public = 1 OR userid = ?) LIMIT 0,1""",
            (playlistid, userid));
        result = cursor.fetchone()
        if result:
            cursor.execute("""SELECT title, url FROM tracks WHERE
                playlistid = ? ORDER BY track ASC""", (playlistid,))
            alltracks = cursor.fetchall()
            apiplaylist = []
            for track in alltracks:
                apiplaylist.append({'title':track[0], 'mp3':track[1]})
            return apiplaylist

    def showPlaylists(self, userid):
        cur = self.conn.cursor()
        #change rowid to id to match api
        cur.execute("""SELECT rowid as id,title FROM playlists WHERE
            public = 1 OR userid = ?""", (userid,));
        return cur.fetchall()

