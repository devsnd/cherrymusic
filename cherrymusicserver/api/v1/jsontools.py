# -*- coding: utf-8 -*- #
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2015 Tom Wallroth & Tilman Boerner
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

""" Utilities for JSON encoding and decoding.
    Hook into the CherryPy's handler tool chain.
"""

#python 2.6+ backward compability
from __future__ import unicode_literals

import json
import sys

import cherrypy

class JSONEncoder(json.JSONEncoder):
    """ JSONEncoder with support for encoding model objects. """
    def default(self, obj):
        try:
            return obj.as_dict()
        except AttributeError:                               # pragma: no cover
            raise TypeError("can't JSON encode %s object %r" % (type(obj), obj))

# see cherrypy._cpcompat.json_encode
_json_encode = JSONEncoder().iterencode
if sys.version_info > (3,):                                  # pragma: no cover
    def json_encode(value):
        for chunk in _json_encode(value):
            yield chunk.encode('UTF-8')
else:
    json_encode = _json_encode                               # pragma: no cover


def json_error_handler(status, message, traceback, version):
    """ CherryPy error handler; turns errors into JSON objects """
    status = str(status)
    code = int(status.split()[0])
    return json_encode(dict(code=code, status=status, message=message, version=version))

def json_handler(*args, **kwargs):
    """ JSON handler that works with cherrypy.tools.json_out """
    value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
    if value is None:
        return None     # return empty body, not "null"
    return json_encode(value)
