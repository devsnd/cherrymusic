-- migrate files

CREATE TABLE _tmp_files_copy(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER DEFAULT 0,
    _deleted INTEGER DEFAULT 0,
    parent INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filetype TEXT,
    isdir INTEGER NOT NULL
);
INSERT INTO _tmp_files_copy(_id, _created, parent, filename, filetype, isdir)
    SELECT rowid, 0, parent, filename, filetype, isdir FROM files;
DROP TABLE files;
ALTER TABLE _tmp_files_copy RENAME TO files;


-- migrate dictionary

CREATE TABLE _tmp_dict_copy(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    occurrences INTEGER NOT NULL DEFAULT 1
);
INSERT INTO _tmp_dict_copy(_id, word, occurrences)
    SELECT rowid, word, occurences FROM dictionary;
DROP TABLE dictionary;
ALTER TABLE _tmp_dict_copy RENAME TO dictionary;


-- migrate search

CREATE TABLE _tmp_search_copy(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    drowid INTEGER NOT NULL,
    frowid INTEGER NOT NULL
);
INSERT INTO _tmp_search_copy(_id, drowid, frowid)
    SELECT rowid, drowid, frowid FROM search;
DROP TABLE search;
ALTER TABLE _tmp_search_copy RENAME TO search;


-- indexes

CREATE INDEX idx_files_parent ON files(parent);
CREATE INDEX idx_dictionary_word ON dictionary(word);
CREATE INDEX idx_search_drowid_frowid ON search(drowid, frowid);    -- for lookup
CREATE INDEX idx_search_frowid_drowid ON search(frowid, drowid);    -- for deletion