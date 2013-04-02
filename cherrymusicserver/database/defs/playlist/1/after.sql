
CREATE UNIQUE INDEX IF NOT EXISTS uidx_playlists_userid_title ON playlists(userid, title);
CREATE INDEX IF NOT EXISTS idx_tracks_playlistid ON tracks(playlistid, track);

CREATE TRIGGER IF NOT EXISTS trigger_playlists_after_delete_purge_tracks
	AFTER DELETE ON playlists
	FOR EACH ROW
	BEGIN
		DELETE FROM tracks WHERE playlistid = old._id;
	END;

CREATE TRIGGER IF NOT EXISTS trigger_playlists_after_update_set_modified
    AFTER UPDATE ON playlists
    FOR EACH ROW
    BEGIN
        UPDATE playlists SET _modified=(strftime('%s', 'now')) WHERE _id = new._id;
    END;