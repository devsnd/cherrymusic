#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
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

import json

from cherrymusicserver import log
from cherrymusicserver import configuration as cfg
from cherrymusicserver import database as db
from cherrymusicserver.database.connect import BoundConnector

DBNAME = 'useroptions'


class UserOptionDB:

    def __init__(self, connector=None):
        """user configuration:
            hidden values can not be set by the user in the options,
            but might be subject of being set automatically, e.g. the
            heartbeat.
        """
        db.require(DBNAME, '0')
        c = cfg.ConfigBuilder()
        with c['keyboard_shortcuts'] as kbs:
            kbs.valid = '\d\d?\d?'
            kbs['prev'].value = 89
            kbs['play'].value = 88
            kbs['pause'].value = 67
            kbs['stop'].value = 86
            kbs['next'].value = 66
            kbs['search'].value = 83
        with c['misc.show_playlist_download_buttons'] as pl_download_buttons:
            pl_download_buttons.value = False
        with c['misc.autoplay_on_add'] as autoplay_on_add:
            autoplay_on_add.value = False
        with c['custom_theme.primary_color'] as primary_color:
            primary_color.value = '#F02E75'
            primary_color.valid = '#[0-9a-fA-F]{6}'
        with c['custom_theme.white_on_black'] as white_on_black:
            white_on_black.value = False
        with c['media.may_download'] as may_download:
            may_download.value = False
        with c['media.force_transcode_to_bitrate'] as force_transcode:
            force_transcode.value = 0
            force_transcode.valid = '0|48|64|96|128|320'
        with c['ui.confirm_quit_dialog'] as confirm_quit_dialog:
            confirm_quit_dialog.value = True
        with c['ui.display_album_art'] as display_album_art:
            display_album_art.value = True
        with c['last_time_online'] as last_time_online:
            last_time_online.value = 0
            last_time_online.valid = '\\d+'
            last_time_online.hidden = True
            last_time_online.doc = "UNIX TIME (1.1.1970 = never)"

        self.DEFAULTS = c.to_configuration()

        self.conn = BoundConnector(DBNAME, connector).connection()

    def getOptionFromMany(self, key, userids):
        result = {}
        for userid in userids:
            val = self.useroptiondb.conn.execute(
                '''SELECT value FROM option WHERE  userid = ? AND name = ?''',
                (userid, key,)).fetchone()
            if val:
                result[userid] = val
            else:
                result[userid] = self.DEFAULTS[key]
        return result

    def forUser(self, userid):
        return UserOptionDB.UserOptionProxy(self, userid)

    class UserOptionProxy:
        def __init__(self, useroptiondb, userid):
            self.useroptiondb = useroptiondb
            self.userid = userid

        def getChangableOptions(self):
            opts = self.getOptions()
            visible_props = (p for p in opts.to_properties() if not p.hidden)
            return cfg.from_list(visible_props).to_nested_dict()

        def getOptions(self):
            results = self.useroptiondb.conn.execute(
                '''SELECT name, value FROM option WHERE userid = ?''',
                (self.userid,)).fetchall()
            useropts = dict((r[0], json.loads(r[1])) for r in results)
            return self.useroptiondb.DEFAULTS.replace(
                useropts,
                on_error=self.delete_bad_option)

        def getOptionValue(self, key):
            return self.getOptions()[key]

        def setOption(self, key, value):
            opts = self.getOptions().replace({key: value})
            self.setOptions(opts)

        def setOptions(self, c):
            for k in cfg.to_list(c):
                value = json.dumps(k.value)
                key = k.key
                sel = self.useroptiondb.conn.execute(
                    '''SELECT name, value FROM option
                        WHERE userid = ? AND name = ?''',
                    (self.userid, key)).fetchone()
                if sel:
                    self.useroptiondb.conn.execute(
                        '''UPDATE option SET value = ?
                            WHERE userid = ? AND name = ?''',
                        (value, self.userid, key))
                else:
                    self.useroptiondb.conn.execute(
                        '''INSERT INTO option (userid, name, value) VALUES
                            (?,?,?)''', (self.userid, key, value))
            self.useroptiondb.conn.commit()

        def deleteOptionIfExists(self, key):
            stmt = """DELETE FROM option WHERE userid = ? AND name = ?;"""
            with self.useroptiondb.conn as conn:
                conn.execute(stmt, (self.userid, key))

        def delete_bad_option(self, error):
            self.deleteOptionIfExists(error.key)
            log.warning('deleted bad option %r for userid %r (%s)',
                        error.key, self.userid, error.msg)
