

CREATE TABLE files(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _deleted INTEGER DEFAULT 0,
    parent INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filetype TEXT,
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
