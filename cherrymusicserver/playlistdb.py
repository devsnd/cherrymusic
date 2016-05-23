#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
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

from cherrymusicserver import database
from cherrymusicserver import log
from cherrymusicserver.cherrymodel import MusicEntry
from cherrymusicserver.database.connect import BoundConnector
try:
    from urllib.parse import unquote
except ImportError:
    from backport.urllib.parse import unquote

DBNAME = 'playlist'

class PlaylistDB:
    def __init__(self, connector=None):
        database.require(DBNAME, version='1')
        self.conn = BoundConnector(DBNAME, connector).connection()

    def deletePlaylist(self, plid, userid, override_owner=False):
        cursor = self.conn.cursor()
        ownerid = cursor.execute(
            "SELECT userid FROM playlists WHERE rowid = ?", (plid,)).fetchone()
        if not ownerid:
            return _("This playlist doesn't exist! Nothing deleted!")
        if userid != ownerid[0] and not override_owner:
            return _("This playlist belongs to another user! Nothing deleted.")
        cursor.execute("""DELETE FROM playlists WHERE rowid = ?""", (plid,))
        self.conn.commit()
        return 'success'

    def savePlaylist(self, userid, public, playlist, playlisttitle, overwrite=False):
        if not len(playlist):
            return _('I will not create an empty playlist. sorry.')
        duplicate_playlist = self.conn.execute(
            """SELECT rowid, public FROM playlists WHERE userid = ? AND title = ?""",
            (userid, playlisttitle)
            ).fetchone()

        if duplicate_playlist:
            if overwrite:
                old_playlist_id, old_public_state = duplicate_playlist
                # saving an existing playlist should keep the same public state:
                public = old_public_state
                self.deletePlaylist(old_playlist_id, userid)
                duplicate_playlist = False
            else:
                return _("This playlist name already exists! Nothing saved.")

        cursor = self.conn.cursor()
        cursor.execute("""INSERT INTO playlists
            (title, userid, public) VALUES (?,?,?)""",
            (playlisttitle, userid, 1 if public else 0))
        playlistid = cursor.lastrowid;
        #put tracknumber to each track
        numberedplaylist = []
        for track, song in enumerate(playlist):
            numberedplaylist.append((playlistid, track, song['url'], song['title']))
        cursor.executemany("""INSERT INTO tracks (playlistid, track, url, title)
            VALUES (?,?,?,?)""", numberedplaylist)
        self.conn.commit()
        return "success"

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
                #TODO ugly hack: playlistdb saves the "serve" dir as well...
                trackurl = unquote(track[1])
                if trackurl.startswith('/serve/'):
                    trackurl = trackurl[7:]
                elif trackurl.startswith('serve/'):
                    trackurl = trackurl[6:]
                apiplaylist.append(MusicEntry(path=trackurl, repr=unquote(track[0])))
            return apiplaylist

    def getName(self, plid, userid ):
        cur = self.conn.cursor()
        cur.execute("""SELECT rowid as id,title FROM playlists WHERE
            (public = 1 OR userid = ?) and rowid=?""", (userid,plid));
        result = cur.fetchall()
        if result:
            return result[0][1]
        return 'playlist'

    def setPublic(self, userid, plid, public):
        ispublic = 1 if public else 0
        cur = self.conn.cursor()
        cur.execute("""UPDATE playlists SET public = ? WHERE rowid = ? AND userid = ?""", (ispublic, plid, userid))
        self.conn.commit()

    def _searchPlaylist(self, searchterm):
        q = '''SELECT DISTINCT playlists.rowid FROM playlists, tracks
               WHERE ( tracks.playlistid = playlists.rowid
                       AND tracks.title LIKE ? )
                     OR
                       playlists.title LIKE ?'''
        cur = self.conn.cursor()
        res = cur.execute(q, ('%'+searchterm+'%', '%'+searchterm+'%'))
        return [row[0] for row in res.fetchall()]

    def showPlaylists(self, userid, filterby='', include_public=True):
        filtered = None
        if filterby != '':
            filtered = self._searchPlaylist(filterby)
        cur = self.conn.cursor()
        select = "SELECT rowid, title, userid, public, _created FROM playlists"
        if include_public:
            where = """ WHERE public=:public OR userid=:userid"""
        else:
            where = """ WHERE userid=:userid"""
        cur.execute(select + where, {'public': True, 'userid': userid});
        results = cur.fetchall()
        playlists = []
        for result in results:
            if not filtered is None and result[0] not in filtered:
                continue
            playlists.append({'plid': result[0],
                              'title': result[1],
                              'userid': result[2],
                              'public': bool(result[3]),
                              'owner': bool(userid==result[2]),
                              'created': result[4]
                              })
        return playlists


    def createPLS(self,userid,plid, addrstr):
        pl = self.loadPlaylist(userid=userid, playlistid=plid)
        if pl:
            plsstr = '''[playlist]
    NumberOfEntries={}
    '''.format(len(pl))
            for i,track in enumerate(pl):
                trinfo = {  'idx':i+1,
                            'url':addrstr+'/serve/'+track.path,
                            'name':track.repr,
                            'length':-1,
                        }
                plsstr += '''
    File{idx}={url}
    Title{idx}={name}
    Length{idx}={length}
    '''.format(**trinfo)
            return plsstr


    def createM3U(self,userid,plid,addrstr):
        pl = self.loadPlaylist(userid=userid, playlistid=plid)
        if pl:
            trackpaths = map(lambda x: addrstr+'/serve/'+x.path,pl)
            return '\n'.join(trackpaths)
