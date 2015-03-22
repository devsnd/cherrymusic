from datetime import datetime
from urllib.parse import unquote

from extlib.peewee import *
from cherrymusicserver.pathprovider import databaseFilePath
from cherrymusicserver.cherrymodel import MusicEntry

db = SqliteDatabase(databaseFilePath('playlist.db'))

class Playlist(Model):
    id = PrimaryKeyField(db_column='rowid')
    _created = DateTimeField(default=datetime.now)
    _modified = DateTimeField(default=datetime.now)
    _deleted = BooleanField(default=False)
    title = CharField()
    userid = IntegerField(null=True)
    public = BooleanField(default=False)

    class Meta:
        database = db
        db_table = 'playlists'

    @classmethod
    def fixUserIds(cls):
        ''' for some reason the userid can be '', so we replace it with 
            the 'nobody' user.
        '''
        db.execute_sql("UPDATE playlists SET userid = 0 WHERE userid = ''")

    @classmethod
    def fetch(cls, playlistid, userid):
        try:
            return Playlist.select().where(
                Playlist.id == playlistid, 
                (Playlist.public == 1) | (Playlist.userid == userid)
            ).get()
        except Playlist.DoesNotExist:
            # playlist does not exist or is not accessible for the user.
            pass

    def set_public(self, public):
        Playlist.update(public=public).where(Playlist.id == self.id).execute()

    def get_tracks(self):
        for track in self.tracks.order_by('track'):
            yield track

    @classmethod
    def search_playlists(cls, term):
        wildcarded = '%' + term + '%'
        playlists = (
            Playlist.select()
            .join(Track)
            .where(
                (Playlist.title ** wildcarded) | (Track.title ** wildcarded)
            )
            .distinct(Playlist.id)
        )
        return playlists

    @classmethod
    def showPlaylists(self, userid, filterby='', include_public=True):
        # DEPRECATED
        # this method only exists for backwards compatiblity
        # use the OO interface instead.
        playlists = Playlist.select()
        if filterby:
            playlists = Playlist.search_playlists(filterby)

        if include_public:
            playlists = playlists.where(
                (Playlist.public == True) | (Playlist.userid == userid)
            )
        else:
            playlists = playlists.where(Playlist.userid == userid)
        return [p.to_dict(userid) for p in playlists]

    def to_dict(self, user_id=None):
        is_owner = False
        if user_id is not None:
            is_owner = self.userid == user_id
        return {
            'plid': self.id,
            'title': self.title,
            'userid': self.userid,
            'public': self.public,
            'owner': is_owner,
            'created': self._created
        }

    @classmethod
    def loadPlaylist(cls, playlistid, userid):
        # DEPRECATED
        # this method only exists for backwards compatiblity
        # use the OO interface instead.
        playlist = Playlist.fetch(playlistid, userid)
        if playlist:
            return [t.to_music_entry() for t in playlist.get_tracks()]

    @classmethod
    def getName(cls, playlistid, userid):
        # DEPRECATED
        # this method only exists for backwards compatiblity
        # use the OO interface instead.
        playlist = Playlist.fetch(playlistid, userid)
        if playlist:
            return playlist.title

    @classmethod
    def setPublic(cls, userid, plid, public):
        # DEPRECATED
        # this method only exists for backwards compatiblity
        # use the OO interface instead.
        playlist = Playlist.fetch(plid, userid)
        if playlist:
            playlist.setPublic(public)

    @classmethod
    def createPLS(cls, userid, plid, addrstr):
        # DEPRECATED
        # this method only exists for backwards compatiblity
        # it should be replaced with an export module
        playlist = Playlist.loadPlaylist(userid=userid, playlistid=plid)
        if playlist:
            header = '[playlist]\nNumberOfEntries={}\n\n'.format(len(playlist))
            entries = []
            for i, track in enumerate(playlist, 1):
                entries.append((
                    'File{idx}={url}\n'
                    'Title{idx}={name}\n'
                    'Length{idx}={length}\n'
                    ).format(
                        idx=i,
                        url='%s/serve/%s' % (addrstr, track.path),
                        name=track.repr,
                        length=-1,
                    )
                )
            return header + '\n'.join(entries)

    @classmethod
    def createM3U(cls, userid, plid, addrstr):
        # DEPRECATED
        # this method only exists for backwards compatiblity
        # it should be replaced with an export module
        playlist = Playlist.loadPlaylist(userid=userid, playlistid=plid)
        if playlist:
            return '\n'.join('%s/serve/%s' % (addrstr, t.path) for t in playlist)


class Track(Model):
    rowid = PrimaryKeyField()
    playlist = ForeignKeyField(Playlist, related_name='tracks', db_column='playlistid')
    track = IntegerField()
    url = TextField()
    title = TextField()

    class Meta:
        database = db
        db_table = 'tracks'

    def to_music_entry(self):
        url = unquote(self.url)
        # TODO, ugly: strip 'serve' directory from the url
        if url.startswith('/serve/'):
            url = url[7:]
        elif url.startswith('serve/'):
            url = url[6:]
        return MusicEntry(path=url, repr=self.title)
