
CREATE TABLE playlists(
	_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	title TEXT,
	userid INTEGER,
	public INTEGER
);

CREATE TABLE tracks(
	_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	playlistid INTEGER,
	track INTEGER,
	url TEXT,
	title TEXT
);

CREATE INDEX idx_tracks_playlistid ON tracks(playlistid);