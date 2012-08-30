#!/usr/bin/python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import hashlib
import sqlite3
import os

import cherrymusic as cherry

USERDBFILE = 'user.db'

class UserDB:
    def __init__(self):
        setupDB = not os.path.isfile(USERDBFILE) or os.path.getsize(USERDBFILE) == 0
        self.conn = sqlite3.connect(USERDBFILE, check_same_thread = False)
        self.salt = cherry.config.crypto.salt.str
        
        if setupDB:
            print('Creating user db table...')
            self.conn.execute('CREATE TABLE users (username text UNIQUE, password text, admin int)')
            self.conn.execute('CREATE INDEX idx_users ON users(username)');
            print('done.')
            print('Connected to Database. ('+USERDBFILE+')')
        
    def addUser(self, username, password, admin):
        if not (username.strip() or password.strip()):
            print('empty username or password!')
            return
        self.conn.execute('''
        INSERT INTO users
        (username, password, admin)
        VALUES (?,?,?)''',
        (username,self.digest(password),1 if admin else 0))
        self.conn.commit()
        msg = 'added user: '+username
        print(msg)
        return msg
        
    def auth(self, username, password):
        if not (username.strip() or password.strip()):
            return self.nobody()
        cur = self.conn.cursor()
        cur.execute('''
        SELECT rowid, username, admin FROM users
        WHERE username = ? and password = ?''',
        (username,self.digest(password)))
        res = cur.fetchone()
        return res if res else self.nobody()
        
    def getUserList(self):
        cur = self.conn.cursor()
        cur.execute('''SELECT rowid, username, admin FROM users''')
        ret = []
        for id,user,admin in cur.fetchall():
            ret.append({'id':id,'username':user,'admin':admin})
        return ret
        
    def getUserCount(self):
        cur = self.conn.cursor()
        cur.execute('''SELECT COUNT(*) FROM users''')
        return cur.fetchall()[0][0]
    
    def saltedpassword(self, password):
        return (password[1::2]+self.salt+password[::2])[::-1]
        
    def digest(self, password):
        saltedpassword_bytes = self.saltedpassword(password).encode('UTF-8')
        return hashlib.sha512(saltedpassword_bytes).hexdigest()
    
    def nobody(self):
        return (-1,None,None)
