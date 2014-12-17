#!/usr/bin/python3
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

import nose

from mock import *
from nose.tools import *

from cherrymusicserver.api.v1.models import Model

def test_model_constructor():
    "Model(**kwargs) should initialize object attributes from kwargs"
    m = Model(id=12, not_a_field=13)
    eq_(12, m.id)
    eq_(13, m.not_a_field)


def test_model_field_defaults():
    "Fix behaviour of default fields and their default values"
    eq_({'id': None, 'cls': 'Model'}, Model().as_dict())

    class Test(Model):
        pass
    eq_('Test', Test().cls)


def test_model_as_dict():
    """ Model.as_dict() should only include field attributes and reflect their
        current value"""
    m = Model(a=11)
    m.id = 12
    m.b = 13
    eq_({'id': 12, 'cls': 'Model'}, m.as_dict())


def test_model_del_field():
    """ Deleting a model object's field attribute should behave like deleting
        a regular attribute without affecting the class or sister objects """
    m = Model()
    del m.cls

    assert_raises(AttributeError, getattr, m, 'cls')
    ok_('cls' not in m.as_dict())

    ok_(Model.cls)
    eq_('Model', Model().cls)


if __name__ == '__main__':
    nose.runmodule()
