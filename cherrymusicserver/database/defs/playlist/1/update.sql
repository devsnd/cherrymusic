--migrate playlists

CREATE TABLE _tmp_playlists_copy (
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _deleted INTEGER DEFAULT 0,
    title TEXT,
    userid INTEGER NOT NULL,
    public INTEGER
);

CREATE UNIQUE INDEX uidx_playlists_userid_title ON playlists(userid, title);

INSERT OR IGNORE INTO _tmp_playlists_copy(_id, title, userid, public)
    SELECT rowid, title, userid, public FROM playlists;

DROP TABLE playlists;

ALTER TABLE _tmp_playlists_copy RENAME TO playlists;


-- migrate tracks

CREATE TABLE _tmp_tracks_copy (
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    playlistid INTEGER NOT NULL,
    track INTEGER,
    url TEXT NOT NULL,
    title TEXT
);

INSERT OR IGNORE INTO _tmp_tracks_copy(playlistid, track, url, title)
    SELECT playlistid, track, url, title FROM tracks;

DROP TABLE tracks;

ALTER TABLE _tmp_tracks_copy RENAME TO tracks;
