
CREATE TABLE users(
	username TEXT UNIQUE,	-- implies index
	admin INTEGER,
	password TEXT,
	salt TEXT
);