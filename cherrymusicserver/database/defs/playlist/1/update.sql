--migrate playlists

CREATE TABLE _tmp_playlists_copy (
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    userid INTEGER,
    public INTEGER
);
INSERT INTO _tmp_playlists_copy
    SELECT rowid, title, userid, public FROM playlists;
DROP TABLE playlists;
ALTER TABLE _tmp_playlists_copy RENAME TO playlists;


-- migrate tracks

CREATE TABLE _tmp_tracks_copy (
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    playlistid INTEGER,
    track INTEGER,
    url TEXT,
    title TEXT
);
INSERT INTO _tmp_tracks_copy(playlistid, track, url, title)
    SELECT playlistid, track, url, title FROM tracks;
DROP TABLE tracks;
ALTER TABLE _tmp_tracks_copy RENAME TO tracks;


-- indexes

CREATE INDEX idx_tracks_playlistid ON tracks(playlistid);