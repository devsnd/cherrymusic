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

import sqlite3
import os
import re
import json

from cherrymusicserver import log
from cherrymusicserver import configuration as cfg

class UserOptionDB:
    
    def __init__(self, USEROPTIONDBFILE):
        """user configuration:
            hidden values can not be set by the user in the options,
            but might be subject of bing set automatically, e.g. the
            heartbeat.
        """
        with cfg.create() as c:
            """with cfg.create('keyboard_shortcuts') as kbs:
                kbs.prev = cfg.Configuration(value='z',validity='\w')
                kbs.play = cfg.Configuration(value='z',validity='\w')
                kbs.pause = cfg.Configuration(value='z',validity='\w')
                kbs.stop = cfg.Configuration(value='z',validity='\w')
                kbs.next = cfg.Configuration(value='z',validity='\w')
                kbs.search = cfg.Configuration(value='z',validity='\w')
                kbs.hidden = False,
                kbs.readonly = False,
                c.keyboard_shortcuts = kbs
            """
            #UNIX TIME (1.1.1970 = never)
            c.last_time_online = cfg.Property(
                value=0,
                name='last_time_online',
                validity='\\d+',
                type='int',
                readonly = False,
                hidden = True
            )
            
            self.DEFAULTS = c
        
        setupDB = not os.path.isfile(USEROPTIONDBFILE) or os.path.getsize(USEROPTIONDBFILE) == 0
        self.conn = sqlite3.connect(USEROPTIONDBFILE, check_same_thread=False)

        if setupDB:
            log.i('Creating user options db table...')
            self.conn.execute('CREATE TABLE option (userid int, name text, value text)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_userid_name ON option(userid, name)')
            log.i('done.')
            log.i('Connected to Database. (' + USEROPTIONDBFILE + ')')

    def getOptionFromMany(self, key, userids):
        result = {}
        for userid in userids:
            val = self.useroptiondb.conn.execute('''SELECT value FROM option WHERE  userid = ? AND name = ?''',(userid, key,)).fetchone()
            if val:
                result[userid] = val
            else:
                result[userid] = self.DEFAULTS[key]['value']
        return result

    def forUser(self, userid):
        return UserOptionDB.UserOptionProxy(self, userid)
        
    class UserOptionProxy:
        def __init__(self, useroptiondb, userid):
            self.useroptiondb = useroptiondb
            self.userid = userid

        def getChangableOptions(self):
            optlist = []
            opts = self.getOptions()
            for c in opts:
                if not opts[c]._hidden:
                   optlist.append((opts[c]['name'], opts[c]['value']))
            return optlist
                    
        
        def getOptions(self):
            results =  self.useroptiondb.conn.execute('''SELECT name, value FROM option WHERE userid = ?''',(self.userid,)).fetchall()
            decoded = []
            for a in results:
                decoded.append((a[0],json.loads(a[1])))
            c = cfg.from_list(decoded)
            c = self.useroptiondb.DEFAULTS + c
            return c
        
        def getOptionValue(self, key):
            return self.getOptions()[key]['value']
        
        def setOption(self, key, value):
            opts = self.getOptions()
            opts[key]['value'] = value
            self.setOptions(opts)
        
        def setOptions(self, c):
            for k in cfg.to_list(c):
                value = json.dumps(k[1])
                key = k[0]
                sel =  self.useroptiondb.conn.execute('''SELECT name, value FROM option WHERE userid = ? AND name = ?''',
                    (self.userid, key)).fetchone()
                if sel:
                    self.useroptiondb.conn.execute('''UPDATE option SET value = ? WHERE userid = ? AND name = ?''',
                        (value, self.userid, key))
                else:
                    self.useroptiondb.conn.execute('''INSERT INTO option (userid, name, value) VALUES (?,?,?)''',
                        (self.userid, key, value))
            self.useroptiondb.conn.commit()
            
    
            
