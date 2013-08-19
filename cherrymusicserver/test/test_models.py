#!/usr/bin/python3
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

from .tools import *

from backport.collections import OrderedDict

from cherrymusicserver.models import *

@model
class Model(object): pass

def create_model(clsname=None, **fields):
    '''
        Create a Model subclass with the given fields and return an instance.

        Fields get created ordered by their default values.
    '''
    from operator import itemgetter
    clsname = clsname or 'TestModel'
    clsdict = OrderedDict()
    for name in (i[0] for i in sorted(fields.items(), key=itemgetter(1))):
        clsdict[name] = field(default=fields[name])
    return model(type(clsname, (object,), clsdict))()


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
        tuple(Model()._as_dict().values()),
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
        '_id': -1,
        '_type': 'model',
    })


def test_model_type_defaults_to_classname():
    eq_('model',
        Model()._type)
    eq_('testmodel',
        create_model('TestModel')._type)


def test_model_dict_view():
    dict_view = create_model(a='test')._as_dict()

    assert isinstance(dict_view, dict)

    eq_(dict_view,
        {'_id': -1, '_type': 'testmodel', 'a': 'test'})


def test_model_dict_idempotence():
    fields = Model._fields
    values = range(len(fields))
    d = dict(zip(fields, values))

    eq_(d,
        Model(**d)._as_dict())


def test_model_equality_to_dicts():
    eq_(Model(),
        Model()._as_dict(),
        "a model must equal its dict view")
    eq_(Model()._as_dict(),
        Model(),
        "a dict must equal a model with equal dict view")


def test_model_constructor_sets_fields_from_params():
    eq_(99,
        Model(99)._id)
    eq_(99,
        Model(_id=99)._id)


def test_model_constructor_assigns_fields_in_order_defined():
    params = '_id _type z a c b'.split()
    values = range(len(params))
    paramdict = dict(zip(params, values))

    testcls = type(create_model(**paramdict))

    eq_(paramdict,
        testcls(*values))


@raises(TypeError)
def test_model_constructor_does_not_accept_nonfield_kwargs():
    Model(bla=99)


@raises(TypeError)
def test_model_constructor_does_not_accept_more_arguments_than_fields():
    args = range(len(Model._fields) + 1)
    Model(*args)


def test_model_subclasses_can_define_own_fields():
    expected = Model._fields + ('a_field',)

    eq_(expected,
        create_model(a_field=None)._fields)


def test_model_subclasses_can_override_fields():
    eq_('type',
        create_model(_type='type')._type)


@raises(AttributeError)
def test_model_subclasses_cannot_override_fields_with_nonfields():
    class Test(Model):
        _id = 12


def test_model_field_string_representation():
    repr(Model._id)


def test_model_field_value_accessible_as_model_attribute():
    eq_(13,
        create_model(a=13).a)


@deprecated
def test_model_field_object_accessible_as_class_attribute():
    assert isinstance(Model._id, Field)


@raises(AttributeError)
def test_model_field_cannot_be_set():
    create_model(a=13).a = 12


def test_fields_compare_in_creation_order():
    f1 = field()
    f2 = field()

    ok_(f1 == f1, 'Field must equal itself')
    ok_(f1 <= f2, 'Field created earlier must compare as less or equal')
    ok_(f2 >= f1, 'Field created later must compare as more or equal')
    ok_(f1 < f2, 'Field created earlier must compare as less')
    ok_(f2 > f1, 'Field created later must compare as more')
    ok_(not f1 != f1, 'Field must not be unequal to itself')


def test_fields_unimplemented_comparison():
    eq_(NotImplemented, field().__lt__(-1))
