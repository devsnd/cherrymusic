CREATE TABLE files(
    _id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER DEFAULT 0,
    _deleted INTEGER DEFAULT 0,
    parent INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filetype TEXT NOT NULL,
    isdir INTEGER NOT NULL
);

CREATE TABLE dictionary(
    _id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    word TEXT NOT NULL,
    occurrences INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE search(
    _id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    drowid INTEGER NOT NULL,
    frowid INTEGER NOT NULL
);


CREATE INDEX idx_files_parent ON files(parent);
CREATE INDEX idx_dictionary_word ON dictionary(word);
CREATE INDEX idx_search_drowid_frowid ON search(drowid, frowid);    -- for lookup
CREATE INDEX idx_search_frowid_drowid ON search(frowid, drowid);    -- for deletion