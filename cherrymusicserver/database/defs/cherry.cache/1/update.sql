-- migrate files

CREATE TABLE _tmp_files_copy(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _deleted INTEGER DEFAULT 0,
    parent INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filetype TEXT,
    isdir INTEGER NOT NULL
);

INSERT INTO _tmp_files_copy(_id, parent, filename, filetype, isdir)
    SELECT rowid, parent, filename, filetype, isdir FROM files;

DROP TABLE files;

ALTER TABLE _tmp_files_copy RENAME TO files;


-- migrate dictionary

CREATE TABLE _tmp_dict_copy(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    occurrences INTEGER NOT NULL DEFAULT 1
);

INSERT INTO _tmp_dict_copy(_id, word)
    SELECT rowid, word FROM dictionary;

UPDATE _tmp_dict_copy SET occurrences = (
    SELECT COUNT(1) FROM search
        WHERE search.drowid = _tmp_dict_copy._id);

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
