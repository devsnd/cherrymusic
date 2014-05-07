#!/usr/bin/env python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
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

import unittest
from nose.tools import raises

try:
    from collections import OrderedDict
except ImportError:
    from backport.collections import OrderedDict

import cherrymusicserver.configuration as cfg
from cherrymusicserver.configuration import Key, Property, Configuration

from cherrymusicserver import log
log.setTest()


class TestKey(object):

    def testConstructor(self):
        assert '' == str(Key())
        assert '' == str(Key(None))
        assert '' == str(Key(str()))
        assert 'a.b' == str(Key('a.b'))
        assert 'a.b' == str(Key('A.B'))

    def testValidation(self):
        for name in '. 1 _ $'.split() + [object()]:
            try:
                Key(name)
            except cfg.ConfigError:
                pass
            else:
                assert False, 'must not accept {0} as Key name'.format(name)

    def testEquals(self):
        assert None == Key()
        assert '' == Key()
        assert Key() == Key()
        assert Key('a') == Key('A')
        assert 'a' == Key('a')
        assert Key('a') != Key('b')
        assert not('a' != Key('A'))

    def testAdd(self):
        assert '' == Key() + Key()
        assert '' == Key() + None
        assert 'string' == Key() + 'string'
        assert 'a.b' == Key('a') + 'b'

    def testRightAdd(self):
        assert 'a.b' == 'a' + Key('b')

    def testAssignAdd(self):
        key = Key('a')
        second_key = key

        second_key += 'b'

        assert key is not second_key
        assert 'a.b' == second_key, (second_key)
        assert 'a' == key, (key)


class TestProperty(object):

    attributes = 'key value type valid readonly hidden doc'.split()

    def test_tupleness_attributes_and_defaults(self):
        """A property is a tuple with named values."""
        default = OrderedDict.fromkeys(self.attributes, None)
        default['key'] = ''
        p = Property()

        assert tuple(default.values()) == p, p
        for attrname, value in default.items():
            assert getattr(p, attrname) == value

    def test_key_is_normalized(self):
        assert 'x.y' == Property('X.Y').key

    def test_type_inferrence(self):
        for T in (bool, int, float, str, type(''),):
            assert T.__name__ == Property(value=T()).type, T

        class UnknownType:
            pass

        assert None == Property(value=UnknownType()).type

        assert 'float' == Property('', 4, float).type

    def test_autocast(self):
        assert 13 == Property('', '13', int).value

    @raises(cfg.ConfigValueError)
    def test_bad_value_for_type(self):
        Property('', 'a', int)

    @raises(cfg.ConfigValueError)
    def test_validation_by_regex(self):
        assert 0 == Property('', 0, valid='[0-9]').value
        Property('', ['x'], valid='[0-9]')

    @raises(cfg.ConfigValueError)
    def test_validation_by_callable(self):
        Property('', False, valid=lambda v: v)

    def test_None_value_is_not_cast_or_validated(self):
        assert None == Property(type=bool, valid=lambda v: v is not None).value

    def test_to_dict(self):
        p = Property('bla', 12, int, '\d+', True, True, '')

        assert p == Property(**p.to_dict())

    def test_replace_without_values(self):
        p = Property('a', 5, int, '\d+', False, False, 'doc')

        assert p == p.replace()
        assert p == p.replace(**dict.fromkeys(self.attributes))

    @raises(cfg.ConfigWriteError)
    def test_cannot_replace_if_readonly(self):
        Property(readonly=True).replace()

    @raises(cfg.ConfigWriteError)
    def test_replace_key(self):
        assert 'different.key' == Property().replace(key='different.key').key
        Property('some.key').replace(key='different.key')

    def test_replace_value(self):
        p = Property(value='original')

        assert 'new' == p.replace(value='new').value
        assert 'original' == p.replace(value=None).value

    def test_replace_type(self):
        assert 'int' == Property().replace(type=int).type
        assert 'int' == Property(type=int).replace(type=str).type

    def test_replace_attributes_only_overridden_if_None(self):
        for attrname in self.attributes[3:]:
            good = {attrname: ''}     # a False value != None to make readonly work
            bad = {attrname: 'unwanted'}
            assert '' == getattr(Property().replace(**good), attrname)
            assert '' == getattr(Property(**good).replace(**bad), attrname)

    def test_immutable(self):
        p = Property()
        assert p is not p.replace(**p.to_dict())

        for attrname in self.attributes:
            try:
                setattr(p, attrname, None)
            except AttributeError:
                pass
            else:
                assert False, 'must not be able to change %r ' % (attrname,)


class TestConfiguration:

    def test_constructor(self):
        from collections import Mapping

        assert isinstance(Configuration(), Mapping)
        assert not len(Configuration())

    def test_equals_works_with_dict(self):
        assert {} == Configuration()
        assert {'a': 1} != Configuration()

    def test_from_and_to_properties(self):
        properties = [Property('a'),
                      Property('a.b', 5, int, '\d+', True, True, 'doc'),
                      Property('b', 5, int, '\d+', True, True, 'doc')]

        conf = Configuration.from_properties(properties)
        assert properties == list(conf.to_properties())
        assert 'a' in conf
        assert 'a.b' in conf
        assert 'b' in conf

    def test_from_mapping(self):
        mapping = {'a': None, 'a.b': 5, 'b': 7}
        assert mapping == Configuration.from_mapping(mapping)

    def test_attribute_access(self):
        p = Property('b', 5, int, '\d+', True, True, 'doc')
        conf = Configuration.from_properties([p])

        assert 5 == conf['b']
        assert p == conf.property('b')

    def test_builder(self):
        properties = [Property('a', 5), Property('a.b', 6, int, '6.*', True, True, 'doc')]
        cb = cfg.ConfigBuilder()

        with cb['a'] as a:
            a.value = 5
            with a['b'] as ab:
                ab.value = 6
                ab.valid = '6.*'
                ab.readonly = True
                ab.hidden = True
                ab.doc = 'doc'

        assert properties == list(cb.to_configuration().to_properties())

    def test_inheritance_of_property_attributes(self):
        cb = cfg.ConfigBuilder()
        with cb['parent'] as parent:
            parent.valid = '.*'
            parent.readonly = True
            parent.hidden = True
            with parent['child'] as child:
                child.value = 4

        childprop = cb.to_configuration().property('parent.child')

        assert '.*' == childprop.valid
        assert childprop.readonly
        assert childprop.hidden

    def test_update(self):
        conf = Configuration.from_properties([Property('b', 'old')])
        newvalues = {'b': 'replaced', 'c': 'new'}
        assert newvalues == conf.update(newvalues)

    def test_replace_changes_existing(self):
        conf = Configuration.from_properties([Property('b', 'old')])
        newvalues = {'b': 'replaced'}
        assert newvalues == conf.replace(newvalues)

    @raises(cfg.ConfigKeyError)
    def test_replace_cannot_add_new(self):
        Configuration().replace({'new': None})


class TestTransformers(unittest.TestCase):

    def test_value_conversions(self):

        def assert_value_conversion(kind, testvalue, expected):
            p = Property('test', testvalue, type=kind)
            actual = p.value
            self.assertEqual(
                expected, actual,
                ('Bad %s conversion for value: %r! expect: %r, actual: %r'
                 % (kind, p.value, expected, actual)))

        def assert_value_conversions(kind, val_exp_pairs):
            for testvalue, expected in val_exp_pairs:
                assert_value_conversion(kind, testvalue, expected)

        assert_value_conversions('str', (('  ', ''),
                                         (None, None),
                                         ))

        assert_value_conversions('int', (('99', 99),
                                         ('-1', -1),
                                         (None, None),
                                         ))

        assert_value_conversions('float', (('99', 99),
                                           ('1.2', 1.2),
                                           ('1.2e3', 1200),
                                           (None, None),
                                           ))

        assert_value_conversions('bool', (('1', True),
                                          ('0', False),
                                          ('Yes', True),
                                          ('Y', True),
                                          ('NO', False),
                                          ('N', False),
                                          ('truE', True),
                                          ('False', False),
                                          ('', False),
                                          (None, None),
                                          ))


if __name__ == "__main__":
    unittest.main()
