#!/usr/bin/env python3
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

""" CherryMusic REST API version 1
    (! under construction !)
"""
#                                      __________
#                                     || .------.|
#                                     ||/       [|
#                                     |||      /||
#                                     |||\    | [|
#                  _     ________ _   |||.'___| |'---...__
#                 /o)===|________(o\  ||========|         ``-..
#                / /       _.----'\ \ |'=.====.='  ________    \
#               / |     .-' ----. / | |  |____|  .'.-------.\   |
#               \  \  .'_.----._ \  | _\_|____|.'.'_.----._ \\__|
#         /\     \  .'.'   __   `.\ |-_| |____| /.'   __   '.\   |
#        // \     \' /   /    \   \\|-_|_|____|//   /    \   \`--'
#       //   \    / .|  |      |  |      |____| |  |      |  |
#      //     \ .'.' |   \ __ /   |             |   \ __ /   |
#     //      /'.'    '.        .'               '.        .'
#    //_____.'-'        `-.__.-'                   `-.__.-' LGB
# http://www.ascii-art.de/ascii/pqr/roadworks.txt (brought to you by the 90s)


#python 2.6+ backward compability
from __future__ import unicode_literals

import sys

import cherrypy

from cherrymusicserver.api.v1 import jsontools
from cherrymusicserver.api.v1 import users
from cherrymusicserver.api.v1.resources import Resource


debug = True


def get_resource():
    """ Assembles and return the API root resource """
    root = ResourceRoot()
    root.users = users.get_resource()
    return root


def get_config():
    """ Return the CherryPy config dict for the API mount point """
    return {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'error_page.default': jsontools.json_error_handler,
            'tools.json_in.on': True,
            'tools.json_out.on': True,
            'tools.json_out.handler': jsontools.json_handler,
            'tools.sessions.on': False,
        },
    }


def mount(mountpath):
    """ Mount and configure API root resource to cherrypy.tree """
    cherrypy.tree.mount(get_resource(), mountpath, config=get_config())

    if sys.version_info < (3,):                               # pragma: no cover
        # Disable a check that crashes the server in python2.
        # Our config keys are unicode, and this check exposes them to an
        # incompatible .translate() call in _cpdispatch.find_handler.
        # (This setting must happen globally through config.update().)
        cherrypy.config.update({
            'checker.check_static_paths': False,
        })


class ResourceRoot(Resource):
    """ Defines the behavior of the API root resource;
        subresources can define their own behavior and should be attached
        dynamically.
    """

    def GET(self):
        """ Returns a list of available subresources """
        resources = []
        for name, member in self.__dict__.items():
            if getattr(member, 'exposed', False):
                resources.append(name)
        return sorted(resources)
