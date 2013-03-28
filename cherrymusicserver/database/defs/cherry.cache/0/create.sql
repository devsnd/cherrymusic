CREATE TABLE files(
    parent INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filetype TEXT NOT NULL,
    isdir INTEGER NOT NULL
);

CREATE TABLE dictionary(
    word TEXT NOT NULL,
    occurences INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE search(
    drowid INTEGER NOT NULL,
    frowid INTEGER NOT NULL
);
