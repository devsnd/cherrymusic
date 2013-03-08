CREATE TABLE _tmp_users_copy(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,	-- implies index
    admin INTEGER,
    password TEXT,
    salt TEXT
);
INSERT INTO _tmp_users_copy
    SELECT rowid, username, admin, password, salt FROM users;
DROP TABLE users;
ALTER TABLE _tmp_users_copy RENAME TO users;
