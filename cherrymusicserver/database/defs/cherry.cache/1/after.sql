CREATE INDEX IF NOT EXISTS idx_files_parent ON files(parent);
CREATE INDEX IF NOT EXISTS idx_dictionary_word ON dictionary(word);
CREATE INDEX IF NOT EXISTS idx_search_drowid_frowid ON search(drowid, frowid);    -- for lookup
CREATE INDEX IF NOT EXISTS idx_search_frowid_drowid ON search(frowid, drowid);    -- for deletion

CREATE TRIGGER IF NOT EXISTS trigger_files_after_update_set_modified
    AFTER UPDATE ON files
    FOR EACH ROW
    BEGIN
        UPDATE files SET _modified=(strftime('%s', 'now')) WHERE _id = new._id;
    END;