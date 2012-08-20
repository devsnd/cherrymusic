import hashlib
import sqlite3
import os

USERDBFILE = 'user.db'

class UserDB:
    def __init__(self, config):
        setupDB = not os.path.isfile(USERDBFILE) or os.path.getsize(USERDBFILE) == 0
        self.conn = sqlite3.connect(USERDBFILE, check_same_thread = False)
        self.config = config
        self.salt = config.config['salt']
        
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
            return nobody()
        cur = self.conn.cursor()
        cur.execute('''
        SELECT rowid, username, admin FROM users
        WHERE username = ? and password = ?''',
        (username,self.digest(password)))
        res = cur.fetchone()
        return res if res else nobody()
        
    def getUserList(self):
        cur = self.conn.cursor()
        cur.execute('''SELECT rowid, username, admin FROM users''')
        ret = []
        for id,user,admin in cur.fetchall():
            ret.append({'id':id,'username':user,'admin':admin})
        return ret
    
    def saltedpassword(self, password):
        return (password[1::2]+self.salt+password[::2])[::-1]
        
    def digest(self, password):
        saltedpassword_bytes = self.saltedpassword(password).encode('UTF-8')
        return hashlib.sha512(saltedpassword_bytes).hexdigest()
    
    def nobody():
        return (-1,None,None)