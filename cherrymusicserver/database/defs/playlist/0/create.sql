CREATE TABLE playlists(
	title TEXT,
	userid INTEGER,
	public INTEGER
);

CREATE TABLE tracks(
	playlistid INTEGER,
	track INTEGER,
	url TEXT,
	title TEXT
);