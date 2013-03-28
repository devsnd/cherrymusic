
CREATE TABLE option(
	userid INTEGER,
	name TEXT,
	value TEXT
);

CREATE INDEX idx_userid_name ON option(userid, name);