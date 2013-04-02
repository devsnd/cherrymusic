CREATE TABLE _tmp_users_copy(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _deleted INTEGER DEFAULT 0,
    username TEXT UNIQUE,	-- implies index
    admin INTEGER,
    password TEXT,
    salt TEXT
);

INSERT INTO _tmp_users_copy(rowid, username, admin, password, salt)
    SELECT rowid, username, admin, password, salt FROM users;

DROP TABLE users;

ALTER TABLE _tmp_users_copy RENAME TO users;
