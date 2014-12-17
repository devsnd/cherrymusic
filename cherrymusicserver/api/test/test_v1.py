#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2014 Tom Wallroth & Tilman Boerner
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

""" CherryMusic Server API integration tests

    Parse API spec file to obtain requests and expected responses, and test
    them against the server.

    Needs ``pyyaml`` for the spec file and ``/usr/bin/curl`` as a convenient
    HTTP client.
"""

from __future__ import unicode_literals

import json
import os
import random
import re
import subprocess
import threading
import time

import cherrypy
import nose
import yaml
# http://pyyaml.org/ticket/59
# def __unicode_str_constructor(loader, node):
#     value = loader.construct_scalar(node)
#     if not isinstance(value, type('')):
#         return value.decode('UTF-8')
#     return value
# yaml.add_constructor('tag:yaml.org,2002:str', __unicode_str_constructor)

from mock import *
from nose.tools import *

from cherrymusicserver.test import helpers

import cherrymusicserver as cms

CHERRYMUSIC_URL = 'http://localhost:{port}/'

def default_specpath():
    filename = 'spec.yml'
    apidir = os.path.dirname(cms.api.v1.__file__)
    return os.path.join(apidir, filename)


def load_spec(filepath=None):
    filepath = filepath or default_specpath()
    with open(filepath) as f:
        rawspec = f.read()
    return yaml.load(rawspec)


def setup_module():
    global _server
    global _spec
    _spec = load_spec()
    _server = APIServer()
    _server.start()
    time.sleep(0.3)             # wait for server to start


def teardown_module():
    _server.stop()


def test_resources():
    srvurl = CHERRYMUSIC_URL.format(port=_server.port)
    baseurl = srvurl.rstrip('/') + '/' + _spec['baseurl'].lstrip('/')
    for respec in _spec['resources'].values():
        for request, expect, response in query_resource(respec, baseurl):
            yield assert_response, request, expect, response


def query_resource(respec, baseurl):
    for case in respec['cases']:
        request = httpblock(case['request'])
        expected = httpblock(case['response'])
        response = send(request, baseurl)
        yield request, expected, response


def assert_response(request, expected, actual):
    """ Assert actual response matches expected.
        request is passed along for context.
    """
    print(request, '\n', expected, '\n', actual)
    eq_(expected.status, actual.status)
    for header in expected.headers:
        assert header in actual.headers, 'missing: ' + header
    if expected.body:
        eq_(json.loads(expected.body), json.loads(actual.body))
    else:
        eq_(expected.body, actual.body)


def send(block, baseurl=''):
    """ Send request contained in httpblock object and return server response
        as another httpblock.
    """
    target = baseurl + block.target
    print('target: %r' % target)
    out, err = curl(target, X=block.method, H=block.headers)
    if err:
        raise RuntimeError(block.method + ' ' + target, err)
    return httpblock(out)


class httpblock(object):
    """ Representation of an HTTP request or response, or a template for one.
        Server responses will be decoded assuming UTF-8 encoding.
    """

    def __init__(self, txtblock):
        self.type = 'Empty Block'
        self.firstline = None
        self.headers = []
        self.body = None
        self.method = None
        self.status = -1
        self.target = None
        try:
            try:
                headers, body = re.split('\r\n\r\n|\n\n', txtblock, maxsplit=1)
            except TypeError:
                headers, body = re.split(b'\r\n\r\n|\n\n', txtblock, maxsplit=1)
                headers = headers.decode('ascii')
                body = body.decode('utf-8')         # assume body is utf-8
        except ValueError:
            self.type = "Bodyless Block"
            headers = txtblock
            body = None
        headers = [h for h in re.split('\r\n|\n', headers) if h.strip()]
        firstline = headers.pop(0)
        word = firstline.split(' ', 1)[0].upper()   # py2-compatible split
        if word.startswith('HTTP'):
            self.type="Server Response"
            self.status = int(firstline.split()[1])
        elif word.isdigit():
            self.type = "Response Template"
            self.status = int(firstline)
        else:
            self.type = "Request Template"
            self.method, self.target = firstline.split(' ', 1)
        self.firstline = firstline
        self.headers = headers
        self.body = body

    def __str__(self):
        txt = ['--- ' + self.type + ' ---']
        txt += [self.firstline] if self.firstline else []
        txt += self.headers
        txt += ['', self.body] if self.body else []
        return '\n'.join(txt)

    def __repr__(self):
        return '%s("""%s""")' % (type(self).__name__, str(self))


def curl(url, **args):
    """ Call ``curl`` with args via subprocess.

    The command and parameters are assembled like this::

        cmd = ['/user/bin/curl', '-i', '-s', '-S']
        cmd.extend(convert(args))
        cmd.append(url)

    `args` get turned into additional command line arguments::

        curl(url, key=v1, k=v2, other_key=v3, switch='')

    will use these additional arguments::

        ['--key', v1, '-k', v2, '--other-key', v3, '--switch', '']

    List values are expanded by repeating the argument:

        args['H'] = [a, b]  -->  ['-H', a, '-H', b]

    """
    cmd = ['/usr/bin/curl', '-i', '-s', '-S']
    for arg, value in args.items():
        arg = ('-' + arg) if len(arg) == 1 else ('--' + arg)
        arg = arg.replace('_', '-')
        if isinstance(value, (list, tuple)):
            for val in value:
                cmd.extend([arg, val])
        else:
            cmd.extend([arg, value])
    cmd.append(url)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    exitcode = proc.wait()
    out, err = proc.communicate()
    if exitcode != 0:
        raise RuntimeError(exitcode, str(cmd), err, out)
    return out, err


class APIServer(threading.Thread):
    """ Wrapper that mounts API module to cherrypy and runs it in a thread

        adapted from
        http://peter.bourgon.org/blog/2009/07/15/a-nontrivial-cherrypy-server-example.html
    """
    def __init__(self):
        self.port = random.randint(2048, 65535)
        threading.Thread.__init__(self)
        self.sync = threading.Condition()

    def run(self):
        with self.sync:
            cherrypy.server.socket_port = self.port
            cherrypy.server.socket_host = 'localhost'
            cms.api.v1.mount('/api/v1')
            cherrypy.engine.start()
        cherrypy.engine.block()

    def stop(self):
        with self.sync:
            cherrypy.engine.exit()
            cherrypy.server.stop()

if __name__ == '__main__':
    nose.runmodule()
