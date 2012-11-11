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

import unittest

from cherrymusicserver import configuration
from cherrymusicserver.configuration import Key, Property, Configuration, ConfigError

from cherrymusicserver import log
log.setTest()


class TestKey(unittest.TestCase):

    def testAdd(self):
        self.assertEquals('', (Key() + Key()).str)
        self.assertEquals('', (Key() + None).str)
        self.assertEquals('string', (Key() + 'string').str)
        self.assertEquals('a.b', (Key('a') + Key('b')).str)

    def testRightAdd(self):
        self.assertEqual('a.b', ('a' + Key('b')).str)

    def testAssignAdd(self):
        key = Key('a')

        with self.assertRaises(NotImplementedError):
            key += 'b'

        self.assertEqual('a', key.str)


    def testEqualsAndHash(self):
        key_ab = Key('a.b')
        key_Ab = Key('A.b')

        self.assertEquals(key_ab, key_Ab)
        self.assertEquals(key_ab, Key('A') + Key('B'))
        self.assertEquals(hash(key_ab), hash(key_Ab))


class TestProperty(unittest.TestCase):

    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_there_are_reserved_words(self):
        self.assertTrue(len(Property._reserved()) > 0)


    def test_reserved_attributes_cannot_be_set(self):
        p = Property('test', value=1)
        self.assertTrue('int' in Property._reserved(), "precondition")

        with self.assertRaises(AttributeError):
            p.int = 9


    def test_nonreserved_attributes_can_be_set(self):
        p = Property('test', 1)
        self.assertFalse('scattermonkey' in Property._reserved(), "precondition")

        p.scattermonkey = 9


    def test_all_public_attributes_names_are_reserved(self):
        public_attributes = set([n for n in dir(Property('test')) if not n.startswith('_')])

        unreserved = public_attributes - set(Property._reserved())

        self.assertTrue(len(unreserved) == 0,
                        '''all public attributes of Configuraion objects must be reserved.
                        unreserved: %s''' % (unreserved,))


    def test_name_must_not_be_reserved(self):
        self.assertTrue('int' in Property._reserved(), "precondition")
        self.assertRaises(ConfigError, Property, name='int')


    def test_name_must_not_be_none_or_empty(self):
        self.assertRaises(ValueError, Property, name=None)
        self.assertRaises(ValueError, Property, name='')


    def test_name_contains_parent_names(self):
        a = Property('a')
        b = Property('a.b')
        c = Property('a.b.c')

        self.assertEqual('a.b.c', c.name, 'property.name must start with parent names')
        self.assertEqual('a', a.name, 'when property without parent, there must be no separator in name')


    def test_readonly_locks_value_and_description(self):
        p = Property('p')
        p.readonly = True

        with self.assertRaises(ConfigError):
            p.value = True
        with self.assertRaises(ConfigError):
            p.desc = "Lala"


    def test_bool_must_equal_value_bool(self):
        self.assertEqual(bool(99), bool(Property('test', 99)))


    def test_int_must_equal_value_int_or_0(self):
        self.assertEqual(int('99'), int(Property('test', '99')))
        self.assertEqual(0, int(Property('test', 'kumquat')))


    def test_float_must_equal_value_float_or_0(self):
        self.assertEqual(float('99.9'), float(Property('test', '99.9')))
        self.assertEqual(0, float(Property('test', 'kumquat')))


    def test_value_conversions(self):

        def assert_value_conversion(kind, testvalue, expected):
            p = Property('test', testvalue)
            actual = p[kind]
            self.assertEqual(expected, actual,
                             ('Bad %s conversion for ' + \
                             'value: %s! expect: %s, actual: %s')
                             % (kind, p.value, expected, actual))

        def assert_value_conversions(kind, val_exp_pairs):
            for testvalue, expected in val_exp_pairs:
                assert_value_conversion(kind, testvalue, expected)

        assert_value_conversions('str', (
                                         ('  ', ''),
                                         (None, ''),
                                         ))

        assert_value_conversions('int', (
                                         ('99', 99),
                                         ('0x10', 16),
                                         ('0o10', 8),
                                         ('1.2', 1),
                                         ('1.2e3', 1200),
                                         ('pomp', 0),
                                         ('cafe', 0),
                                         (None, 0),
                                         ))

        assert_value_conversions('float', (
                                         ('99', 99),
                                         ('0x10', 16),
                                         ('0o10', 8),
                                         ('pomp', 0),
                                         ('1.2', 1.2),
                                         ('1.2e3', 1200),
                                         (None, 0),
                                         ))

        assert_value_conversions('bool', (
                                          ('1', True),
                                          ('0', False),
                                          ('0x1', True),
                                          ('Yes', True),
                                          ('NO', False),
                                          ('truE', True),
                                          ('False', False),
                                          ('pomp', False),
                                          (None, False),
                                          ))

        assert_value_conversions('list', (
                                          ('Fee fi, fo_fum!', ['Fee', 'fi', 'fo', 'fum']),
                                          (None, []),
                                          ))


class TestConfiguration(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_name_must_be_consistent_with_init(self):
        self.assertEqual('testname', Configuration('testname').name)

    #TODO replace with proper test for confuration.to_list
    @unittest.skip
    def test_list(self):
        '''list transformer must return a list of Property tuples'''
        c = Configuration()
        c.A = '1'
        c.a.desc = 'a.1'
        c.b.x = '2'
        c.b.x.desc = 'b.x.2'

        l = c.list

        self.assertTrue(len(l) == 2,
                        'list must contain exactly 2 Property tuples, but is %s' % l)
        self.assertTrue(('A', '1', 'a.1') in l, l)
        self.assertTrue(('b.x', '2', 'b.x.2') in l, l)


    #TODO replace with proper test for confuration.to_dict
    @unittest.skip
    def test_dir(self):
        '''dict transformer must return a dict conforming to a dict that might
        have been used for initialization'''
        d = {'a':1, 'b':2}
        c = configuration.from_dict(d)

        self.assertDictEqual(d, c.dict, '')


    def test_all_public_attributes_names_are_reserved(self):
        public_attributes = set([n for n in dir(Configuration()) if not n.startswith('_')])

        unreserved = public_attributes - set(Property._reserved())

        self.assertTrue(len(unreserved) == 0,
                        '''all public attributes of Configuraion objects must be reserved.
                        unreserved: %s''' % (unreserved,))


    def test_delete_deletes_only_one_element(self):
        cfg = configuration.from_dict({'a' : {
                                              'x': 11,
                                              },
                                       'b' : 3,
                                       })

        del cfg['a.x']

        self.assertEqual(2, len(cfg))
        self.assertTrue('a' in cfg)
        self.assertTrue('b' in cfg)
        self.assertFalse('a.x' in cfg)


    def test_assignment(self):
        initdict = {
            'a': {
                  'x':11,
                  },
            'b': 3,
            }
        cfg = configuration.from_dict(initdict)

        cfg.a = 2
        self.assertEquals(2, cfg.a.value)

        cfg.p = Property('x', value=7, valtype='int', readonly=True, hidden=True, validity=r'\d+', desc='integer')


if __name__ == "__main__":
    unittest.main()
