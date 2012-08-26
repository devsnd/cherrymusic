import hashlib
import sqlite3
import os
import uuid

from collections import namedtuple

USERDBFILE = 'user.db'

class UserDB:
    def __init__(self):
        setupDB = not os.path.isfile(USERDBFILE) or os.path.getsize(USERDBFILE) == 0
        self.conn = sqlite3.connect(USERDBFILE, check_same_thread=False)

        if setupDB:
            print('Creating user db table...')
            self.conn.execute('CREATE TABLE users (username text UNIQUE, admin int, password text, salt text)')
            self.conn.execute('CREATE INDEX idx_users ON users(username)');
            print('done.')
            print('Connected to Database. (' + USERDBFILE + ')')

    def addUser(self, username, password, admin):
        if not (username.strip() or password.strip()):
            print('empty username or password!')
            return
        user = User.create(username, password, admin)
        self.conn.execute('''
        INSERT INTO users
        (username, admin, password, salt)
        VALUES (?,?,?,?)''',
        (user.name, 1 if user.isadmin else 0, user.password, user.salt))
        self.conn.commit()
        msg = 'added user: ' + user.name
        print(msg)
        return msg

    def auth(self, username, password):
        if not (username.strip() or password.strip()):
            return User.nobody()
        cur = self.conn.execute('''
        SELECT rowid, username, admin, password, salt FROM users
        WHERE username = ?''', (username,))
        user = User.nobody()
        while True:
            row = cur.fetchone()
            if row:
                user = User(*row)
                login = Crypto.scramble(password, user.salt) == user.password
            if not row or login:
                break
        return user

    def getUserList(self):
        cur = self.conn.cursor()
        cur.execute('''SELECT rowid, username, admin FROM users''')
        ret = []
        for uid, user, admin in cur.fetchall():
            ret.append({'id':uid, 'username':user, 'admin':admin})
        return ret

    def getUserCount(self):
        cur = self.conn.cursor()
        cur.execute('''SELECT COUNT(*) FROM users''')
        return cur.fetchall()[0][0]


class Crypto(object):

    @classmethod
    def generate_salt(cls):
        '''returns a random hex string'''
        return uuid.uuid4().hex

    @classmethod
    def salted(cls, plain, salt):
        '''interweaves plain and salt'''
        return (plain[1::2] + salt + plain[::2])[::-1]

    @classmethod
    def scramble(cls, plain, salt):
        '''returns a sha512-hash of plain and salt as a hex string'''
        saltedpassword_bytes = cls.salted(plain, salt).encode('UTF-8')
        return hashlib.sha512(saltedpassword_bytes).hexdigest()


class User(namedtuple('User_', 'uid name isadmin password salt')):

    __NOBODY = None

    @classmethod
    def create(cls, name, password, isadmin=False):
        '''create a new user with given name and password. will add a random salt.'''

        if not name.strip():
            raise ValueError('name must not be empty')
        if not password.strip():
            raise ValueError('password must not be empty')

        salt = Crypto.generate_salt()
        password = Crypto.scramble(password, salt)
        return User(-1, name, password, salt, isadmin)


    @classmethod
    def nobody(cls):
        '''return a user object representing an unknown user'''
        if User.__NOBODY is None:
            User.__NOBODY = User(-1, None, None, None, False)
        return User.__NOBODY
