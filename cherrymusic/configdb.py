import os
import sqlite3

import cherrymusic.configuration

from cherrymusic.configuration import Configuration
from cherrymusic import configuration

CONFIGDBFILE = 'config.db'
#CONFIGDBFILE = ':memory:'

class ConfigDB(object):
    """quick and dirty implementation of a config database in sqlite3"""

    def __init__(self):
        setupDB = not os.path.isfile(CONFIGDBFILE) or os.path.getsize(CONFIGDBFILE) == 0
        self.conn = sqlite3.connect(CONFIGDBFILE, check_same_thread=False)

        if setupDB:
            print('Creating config db table...')
            self.conn.execute('CREATE TABLE config (key text UNIQUE, value text)')
            self.conn.execute('CREATE INDEX idx_config ON config(key)');
            print('done.')
            print('Initializing config db with default configuration...')
            self.reset_to_default()
            print('done.')
            print('Connected to Database. (' + CONFIGDBFILE + ')')

    def load(self):
        cursor = self.conn.execute('SELECT * FROM config')
        dic = {}
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            key, value = row
            dic[key] = value
        return Configuration(dic=dic)

    def save(self, cfg, clear=False):
        """save cfg to database. clear==True replaces existing config completely. clear=False behaves like update."""
        if clear:
            self.conn.execute('DELETE FROM config')
            self._dump(cfg)
        else:
            self.update(cfg)

    def update(self, cfg):
        """updates config database from cfg. entries in cfg overwrite existing keys or are created new.
        existing entries not in cfg remain untouched."""
        if cfg:
            for key, value in cfg.list:
                foundid = self.conn.execute('SELECT rowid FROM config WHERE key=?', (key,)).fetchone()
                if foundid is None:
                    self.conn.execute('INSERT INTO config (key, value) VALUES (?,?)', (key, value))
                else:
                    foundid = foundid[0]
                    self.conn.execute('UPDATE config SET key=?, value=? WHERE rowid=?', (key, value, foundid))
            self.conn.commit()

    def reset_to_default(self):
        '''clears all content from the database and reinitializes it with default values'''
        self.save(configuration.from_defaults(), clear=True)

    def _dump(self, cfg):
        if cfg:
            for key, value in cfg.list:
                self.conn.execute('INSERT INTO config (key, value) VALUES (?,?)', (key, value))
            self.conn.commit()
