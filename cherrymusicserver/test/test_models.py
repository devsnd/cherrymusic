#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2013 Tom Wallroth & Tilman Boerner
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

from mock import *
from nose.tools import *

from collections import namedtuple

from .tools import *

from cherrymusicserver.models import *

def create_model(clsname=None, **fields):
    clsname = clsname or 'TestModel'
    modelcls = model(clsname, **fields)
    return modelcls()

def test_model_string_representation():
    repr(Model())


def test_model_equality_to_other_models():
    model = Model()

    eq_(model,
        model,
        "a model must equal itself")

    eq_(Model(),
        Model(),
        "equal models must be equal")

    assert not model != model, "a model must not be unequal to itself"
    assert not Model() != Model(), "equal models must not be unequal"


def test_unimplemented_equality():
    examples = [
        tuple(Model().as_dict.values()),
    ]
    for case in examples:
        eq_(NotImplemented,
            Model().__eq__(case))

@raises(TypeError)
def test_model_is_not_hashable():
    hash(Model())


def test_model_universal_field_present_with_defaults():
    eq_(Model(),
        {
        '_id': None,
        '_type': 'model',
    })


def test_model_type_defaults_to_classname():
    eq_('model',
        Model()._type)
    eq_('testmodel',
        create_model('TestModel')._type)


def test_model_dict_view():
    dict_view = create_model(a='test').as_dict

    assert isinstance(dict_view, dict)

    eq_(dict_view,
        {'_id': None, '_type': 'testmodel', 'a': 'test'})


def test_model_dict_idempotence():
    fields = Model._fields
    values = range(len(fields))
    d = dict(zip(fields, values))

    eq_(d,
        Model(**d).as_dict)


def test_model_equality_to_dicts():
    eq_(Model(),
        Model().as_dict,
        "a model must equal its dict view")
    eq_(Model().as_dict,
        Model(),
        "a dict must equal a model with equal dict view")


def test_model_constructor_sets_fields_from_params():
    eq_(99,
        Model(_id=99)._id)

def test_model_constructor_turns_nonfield_kwargs_into_fields():
    m = Model(bla=99)

    eq_(99,
        m.bla)
    assert 'bla' in m._fields

@raises(TypeError)
def test_model_constructor_does_not_accept_more_arguments_than_fields():
    args = range(len(Model._fields) + 1)
    Model(*args)


def test_model_subclasses_can_define_own_fields():
    expected = set(Model._fields + ('a_field',))

    eq_(expected,
        create_model(a_field=None)._fields)


def test_model_subclasses_can_override_fields():
    eq_('type',
        create_model(_type='type')._type)

def test_model_subclasses_can_override_fields_with_nonfields():
    class Test(Model):
        _id = 12

    eq_(12, Test()._id)


def test_model_field_string_representation():
    repr(Model._id)


def test_model_field_value_accessible_as_model_attribute():
    eq_(13,
        create_model(a=13).a)


def test_model_field_can_be_set():
    m = create_model(a=13)
    eq_(13, m.a)

    m.a = 12

    eq_(12, m.a)


def test_fields_doc_attribute_is_also_docstring():
    eq_('a docstring',
        field(doc='a docstring').__doc__)
    eq_('a docstring',
        field(doc='a docstring').doc)


def test_model_can_extend_namedtuple():
    TestModel = model(namedtuple('TestModel', 'a b'))

    m = TestModel(1,2)

    eq_({'a': 1, 'b': 2}, m.as_dict)


def test_model_can_extend_other_models():
    @model
    class TestModel(Model):
        heya = field()

    eq_(('_id', '_type', 'heya'), TestModel._fields)
