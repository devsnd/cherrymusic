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

from cherrymusicserver import log

class UserOptionDB:
    
    def __init__(self, USEROPTIONDBFILE):
        self.defaults = {
            'keyboard_shortcuts' : {
                #possible types are: list, str, int
                'type' : list,
                'value': ['PREV:z','PLAY:x','PAUSE:c','STOP:v','NEXT:b','SEARCH:s'], #winamp like defaults
                'validation' : '[A-Z]:.*', #re.match performed on value/each value in list
                'readonly' : False,
                'hidden' : False,
            }
        }
        
        setupDB = not os.path.isfile(USEROPTIONDBFILE) or os.path.getsize(USEROPTIONDBFILE) == 0
        self.conn = sqlite3.connect(USEROPTIONDBFILE, check_same_thread=False)

        if setupDB:
            log.i('Creating user options db table...')
            self.conn.execute('CREATE TABLE option (userid id UNIQUE, name text, type text, value text)')
            #TODO: create INDEXES?
            log.i('done.')
            log.i('Connected to Database. (' + USEROPTIONDBFILE + ')')

    def getOption(self, userid, optionname):
        if optionname in self.defaults:
            opt = self.__getOptionFromDB(userid,optionname)
            if opt:
                return opt
            return self.defaults[optionname]
        return None
    
    def setOption(self, userid, optionname, value):
        isSane, reason = self.__isSaneOption(optionname, value)
        if isSane:
            if self.defaults[optionname].get('readonly',False):
                log.e('user with id %s tried to set readonly option %s!' % (userid, optionname))
                return False
                
            if self.__getOptionFromDB(userid,optionname):
                self.__updateOptionInDB(userid, optionname, value)
                return True
            else:
                self.__setOptionInDB(userid, optionname, value)
                return True
        else:
            if reason == 'unknown option':
                log.e('user with id %s tried to set unknown option %s!' % (userid, optionname))
            elif reason == 'invalid value':
                log.e('user with id %s tried to set option %s to invalid value!' % (userid, optionname))
            elif reason == 'invalid type':
                log.e('user with id %s tried to set option %s with invalid type!' % (userid, optionname))
            return False
            
    def __isSaneOption(self, optionname, value):
        if not optionname in self.defaults:
            return False, 'unknown option'
        if type(value) != self.defaults[optionname]['type']:
            return False, 'invalid type'
        if type(value) == list:
            for e in value:
                if not re.match(self.defaults['validation'],value):
                    return False, 'invalid value'
        else:
            if not re.match(self.defaults['validation'],value):
                return False, 'invalid value'
        return True
    
    def __updateOptionInDB(self, userid, optionname, value):
        self.conn.execute('''UPDATE option SET value=? WHERE userid=? AND name=?''',
            (value, userid, optioname))
    
    def __setOptionInDB(self, userid, optionname, value):
        self.conn.execute('''
        INSERT INTO option
        (userid, name, value)
        VALUES (?,?,?)''',
        (userid, optionname, value))

    def __getOptionFromDB(self, userid, optionname):
        res = self.conn.execute('''SELECT value FROM option 
        WHERE userid = ? AND name = ?''',(userid, optionname))
        if res:
            return res[0]
        return None
        
    