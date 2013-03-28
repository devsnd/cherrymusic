
CREATE TABLE playlists(
	_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _deleted INTEGER DEFAULT 0,
	title TEXT,
	userid INTEGER NOT NULL,
	public INTEGER
);

CREATE TABLE tracks(
	_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	playlistid INTEGER NOT NULL,
	track INTEGER,
	url TEXT NOT NULL,
	title TEXT
);
