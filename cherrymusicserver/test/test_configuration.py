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
        self.assertEqual('', (Key() + Key()).str)
        self.assertEqual('', (Key() + None).str)
        self.assertEqual('string', (Key() + 'string').str)
        self.assertEqual('a.b', (Key('a') + Key('b')).str)

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

        self.assertEqual(key_ab, key_Ab)
        self.assertEqual(key_ab, Key('A') + Key('B'))
        self.assertEqual(hash(key_ab), hash(key_Ab))


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


    def test_name_contains_parent_names(self):
        a = Property('a')
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


    def test_validation(self):

        p = Property('test')
        p.value = object()  # uninitialized validation must allow all, including weird, values

        '''can't re-set validity string'''
        with self.assertRaises(AttributeError):
            p.validity = 'something'

        '''validation takes place in constructor'''
        with self.assertRaises(ValueError):
            Property('test', validity='brai+ns!')


        ### REGULAR EXPRESSIONS

        self.assertEqual('braiiins!', Property('test', 'braiiins!', validity='brai+ns!').value,
                         'validation is through regex')

        '''validation is by match, not by find'''
        with self.assertRaises(ValueError):
            Property('test', 'halfbrains!', validity='brai+ns!')

        '''validation is by full match'''
        with self.assertRaises(ValueError):
            Property('test', 'brains! supple brains!', validity='brai+ns!')


        ### NON-STRING VALUES

        self.assertEqual(99, Property('test', 99, validity='\d+').value,
                         'validation str(ingifies) value temporarily')


        ### WHITESPACE 

        self.assertEqual('brains!', Property('test', '\f\n\r\t\vbrains! ', validity='brai+ns!').value,
                         'validation trims whitespace from value')

        self.assertEqual('brains!', Property('test', 'brains!', validity='  brai+ns!\f\n\r\t\v').value,
                         'validation trims whitespace from validity expression')

        '''validation respects explicit whitespace in regex'''
        with self.assertRaises(ValueError):
            Property('test', '\f\n\r\t\v XY ', validity=r'\f\n\r\t\v XY\s') # invalid because value gets trimmed

        self.assertEqual('brains!', Property('test', 'brains!', validity=' ^ brai+ns! $ ').value,
                         'leading ^ and trailing $ is ignored, even if embedded in whitespace')


        ### LISTS

        '''empty list must be ok'''
        p = Property('', type='list', validity='\d+')

        '''value must be validated as list'''
        p.value = ' 1, 123   '

        with self.assertRaises(ValueError):
            p.value = '1, 123, None'




    def test_typechecks_and_type_effects(self):

        ### CONSTRUCTOR

        self.assertEqual(11, Property('test', 11).value,
                         'without type, the value remains untransformed')

        self.assertEqual(11, Property('test', 11.5, type='int').value,
                         'with type, the value is transformed')

        self.assertEqual('', Property('test', None, type='str').value,
                         'with type, the value is transformed')

        self.assertRaises(configuration.TransformError, configuration.Transformers['int'], None)
        self.assertEqual(0, Property('test', None, type='int').value,
                         'with type, trying to set None sets Transformer default')

        self.assertFalse(Property('test', type='FRXMBL').type,
                        'unknown type will default to no type')


        ### ASSIGNMENT

        ## with type ##

        p = Property('test', type='int')

        '''can assign convertible values'''
        p.value = '0x10'
        self.assertEqual(16, p.value)

        '''can't assign inconvertible objects'''
        self.assertRaises(configuration.TransformError, configuration.Transformers['int'], object())
        with self.assertRaises(TypeError):
            p.value = object()

        '''assigning None works though and goes to default'''
        p.value = None
        self.assertEqual(0, p.value)


        ## without type  ##

        '''without value set, any crap can be assigned'''
        no_type = Property('no.type')
        crap = object()
        no_type.value = crap
        self.assertEqual(crap, no_type.value)

        '''with transformable-type value set, new value will be transformed or not accepted'''
        no_type = Property('no.type', 0)
        no_type.value = 3.14
        self.assertEqual(3, no_type.value)
        with self.assertRaises(TypeError):
            no_type.value = 'not an int'

        '''with non-transformable-type value set, can assign value of same type'''
        no_type = Property('no.type', object())
        no_type.value = 3.14
        self.assertEqual(3.14, no_type.value)

        '''with non-transformable-type  value set, can't assign different type'''
        no_type = Property('no.type', type(object))
        with self.assertRaises(TypeError):
            no_type.value = 3.14


    def test_bool(self):
        self.assertFalse(bool(Property('')),
                         'empty Property must be False')
        self.assertFalse(bool(Property('some_name')),
                        'property with just a name must be False')

        self.assertTrue(bool(Property('', value=11)),
                        'property with a set value must be True')
        self.assertTrue(bool(Property('', type='int')),
                        'property with a type must be True')
        self.assertTrue(bool(Property('', hidden=True)),
                        'hidden property must be True')
        self.assertTrue(bool(Property('', readonly=True)),
                        'readonly property must be True')
        self.assertTrue(bool(Property('', validity='.*')),
                        'property with set vailidity must be True')
        self.assertTrue(bool(Property('', desc='bla')),
                        'property with a description must be True')


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

    def test_constructor(self):

        a = Configuration('a', 5, 'int', validity='\d+', desc='bla', readonly=True, hidden=True)

        self.assertEqual('a', a.name)
        self.assertEqual(5, a.value)
        self.assertEqual('int', a.type)
        self.assertEqual(True, a.readonly)
        self.assertEqual(True, a.hidden)
        self.assertEqual('\d+', a.validity)
        self.assertEqual('bla', a.desc)

        c = Configuration()
        d = Configuration('d', 5, 'int', validity='\d+', desc='bla', parent=c)
        e = Configuration('e', parent=d)
        c.hidden = True
        c.readonly = True

        self.assertEqual('', c.name)
        self.assertEqual(None, c.value)
        self.assertEqual('', c.type)
        self.assertEqual(True, c.readonly)
        self.assertEqual(True, c.hidden)
        self.assertEqual('', c.validity)
        self.assertEqual('', c.desc)

        self.assertEqual('d', d.name)
        self.assertEqual(5, d.value)
        self.assertEqual('int', d.type)
        self.assertEqual(True, d.readonly)
        self.assertEqual(True, d.hidden)
        self.assertEqual('\d+', d.validity)
        self.assertEqual('bla', d.desc)

        self.assertEqual('d.e', e.name)


    def test_name(self):
        root = Configuration('root')
        self.assertEqual('root', root.name,
                         'root config name must match init parameter')

        first = Configuration('first', parent=root)
        self.assertEqual('root.first', first.name,
                         'non-root name must be fully qualified')

        second = Configuration('second', parent=first)
        self.assertEqual('root.first.second', second.name,
                         'non-root name must be fully qualified')

        root = Configuration()
        self.assertEqual('', root.name,
                         'root config name must be empty if no name set')

        first = Configuration('first', parent=root)
        self.assertEqual('first', first.name,
                         'non-root name must be fully qualified')

        second = Configuration('second', parent=first)
        self.assertEqual('first.second', second.name,
                         'non-root name must be fully qualified')


    def test_list(self):
        '''list transformer must return a list of Property tuples'''

        with configuration.create() as c:
            c.A = '1'
            c.a.desc = 'a.1'
            c.b.x = Property('b.x', 2, 'int', '\d+', True, True, 'b.x.2')
            c.b.f = 'defined second, alphabetically first'

        l = configuration.to_list(c)

        self.assertEqual(3, len(l),
                        'list must contain exactly 3 Property tuples, but is %s' % l)
        self.assertEqual(('A', '1', '', '', None, None, 'a.1'), l[0])
        self.assertEqual(('b.x', 2, 'int', '\d+', True, True, 'b.x.2'), l[1])
        self.assertEqual(('b.f', 'defined second, alphabetically first', '', '', None, None, ''), l[2])


    def test_dir(self):
        '''dict transformer must return a dict conforming to a dict that might
        have been used for initialization'''

        d = {'a':1, 'b':2, 'c': {
                                 'value': 3,
                                 'hidden': True,
                                 'readonly': True,
                                 'type': 'int',
                                 'validity': '\d+',
                                 'd': {'e': 55},
                                 }}

        with configuration.create() as c:
            c.a = 1
            c.b = 2
            c.c = Configuration('c', 3, type='int', validity='\d+', hidden=True)
            c.c.d.e = 55
            c.c.readonly = True

        self.assertDictEqual(d, configuration.to_dict(c))

        cfg = configuration.from_dict(d)

        self.assertEqual(1, cfg.a.value)
        self.assertEqual(2, cfg.b.value)
        self.assertEqual(3, cfg.c.value)
        self.assertEqual('int', cfg.c.type,)
        self.assertEqual(True, cfg.c.readonly)
        self.assertEqual(True, cfg.c.hidden)
        self.assertEqual('\d+', cfg.c.validity)
        self.assertEqual(55, cfg.c.d.e.value)


    def test_all_public_attributes_names_are_reserved(self):
        public_attributes = set([n for n in dir(Configuration()) if not n.startswith('_')])

        unreserved = public_attributes - set(Property._reserved())

        self.assertTrue(len(unreserved) == 0,
                        '''all public attributes of Configuraion objects must be reserved.
                        unreserved: %s''' % (unreserved,))


    def test_delete_deletes_only_one_element(self):
        cfg = configuration.from_dict({'a' : {'x': 11, },
                                       'b' : 3, })

        del cfg['a.x']

        self.assertEqual(2, len(cfg), repr(cfg))
        self.assertTrue('a' in cfg)
        self.assertTrue('b' in cfg)
        self.assertFalse('a.x' in cfg)


    def test_mapping_contains_len_and_iter(self):
        with configuration.create() as cfg:
            # contains
            self.assertFalse(None in cfg)
            self.assertFalse('' in cfg)
            self.assertFalse('a' in cfg)

            cfg['a'] = 'something'
            self.assertTrue('a' in cfg)

            cfg['b']['c'] = 'something'
            self.assertTrue('b' in cfg)
            self.assertTrue('b.c' in cfg)

            # iter
            self.assertEqual(['a', 'b', 'b.c'], [k for k in cfg])

            # len
            self.assertEqual(3, len(cfg))
            self.assertEqual(0, len(Configuration()))


    def test_basic_access(self):
        with configuration.create() as cfg:
            cfg['a'] = 11
            self.assertEqual(11, cfg['a'].value,
                             'one-level get and set')

            cfg['a']['b'] = 13
            self.assertEqual(13, cfg['a']['b'].value,
                             'multi-level get and set')

            cfg['a']['x']['c'] = 17
            self.assertEqual(17, cfg['a']['x']['c'].value,
                             'can set subkey of non-existant key')
            self.assertTrue('a.x' in cfg,
                             'accessing a key creates it')

            cfg['x']
            self.assertTrue('x' in cfg,
                            'accessing a key creates it, even without any assignment happening')

            del cfg['x']
            self.assertFalse('x' in cfg,
                             'deleting a key removes it')

            del cfg['a']
            self.assertEqual(0, len(cfg),
                             'deleting a key must also delete all subkeys')


    def test_simplified_multi_access(self):
        with configuration.create() as cfg:

            cfg['a.b'] = 11
            self.assertEqual(11, cfg['a']['b'].value,
                             'multilevel set')
            self.assertEqual(11, cfg['a.b'].value,
                             'multilevel get')
            self.assertEqual(11, cfg['a.b.value'],
                             'multilevel get down to Property attribute')

            cfg['c.value'] = 'mrx'
            self.assertEqual('mrx', cfg['c'].value,
                             'multilevel set, down to Property attribute')

            del cfg['c.desc']
            self.assertFalse(cfg['c'].desc,
                             'multilevel del, down to Property attribute')

            del cfg['a.b']
            self.assertEqual(['a', 'c'], [k for k in cfg],
                             'multilevel del')


    def test_attribute_access(self):
        with configuration.create() as cfg:
            cfg.a = 11
            self.assertEqual(11, cfg['a'].value,
                             'set via attribute')
            self.assertEqual(11, cfg.a.value,
                             'get via attribute')

            cfg.b.c.value = 19
            self.assertEqual(19, cfg.b.c.value,
                             'multilevel get and set via attribute')
            self.assertEqual(None, cfg.b.value,
                             'yes, b got created, too')

            del cfg.b.c
            self.assertFalse('b.c' in cfg,
                             'multilevel del')


    def test_errors_for_undefined_keys(self):
        cfg = Configuration()

        with self.assertRaises(KeyError):
            cfg['a']
        with self.assertRaises(AttributeError):
            cfg.a
        with self.assertRaises(AttributeError):
            cfg.a = 9
        with self.assertRaises(AttributeError):
            cfg.b.desc = 'schweinebacke'


    def test_hidden_and_readonly_parent_overrules_child(self):

        with configuration.create() as parent:
            parent.child
            parent.child.subchild

        self.assertFalse(parent.hidden)
        self.assertFalse(parent.readonly)
        self.assertFalse(parent.child.hidden)
        self.assertFalse(parent.child.readonly)
        self.assertFalse(parent.child.subchild.hidden)
        self.assertFalse(parent.child.subchild.readonly)

        parent.hidden = True
        parent.readonly = True
        self.assertTrue(parent.child.hidden)
        self.assertTrue(parent.child.readonly)
        self.assertTrue(parent.child.subchild.hidden)
        self.assertTrue(parent.child.subchild.readonly)


    def test_merge(self):

        with configuration.create() as c:
            d = Configuration('d', 5, 'int', readonly=True, hidden=True, validity='\d+', desc='bla')

            c.d = d
            self.assertEqual('d', c.d.name)
            self.assertEqual(5, c.d.value)
            self.assertEqual('int', c.d.type)
            self.assertEqual(True, c.d.readonly)
            self.assertEqual(True, c.d.hidden)
            self.assertEqual('\d+', c.d.validity)
            self.assertEqual('bla', c.d.desc)

            c.e.readonly = True
            with self.assertRaises(ConfigError):
                c.e = 11

            c.v = 11
            self.assertEqual(11, c.v.value)

            c.v.f = Property('v.f', 5, 'int', readonly=True, hidden=True, validity='\d+', desc='bla')
            self.assertEqual('v.f', c.v.f.name)
            self.assertEqual(5, c.v.f.value)
            self.assertEqual('int', c.v.f.type)
            self.assertEqual(True, c.v.f.readonly)
            self.assertEqual(True, c.v.f.hidden)
            self.assertEqual('\d+', c.v.f.validity)
            self.assertEqual('bla', c.v.f.desc)

            with self.assertRaises(ConfigError):
                c.x = Property('NOT.X')

        'merging is atomic'
        with configuration.create() as c:
            e = Configuration('e', 0, type='int')
            c.e = e
        with self.assertRaises(ConfigError):
            c.e = Property('e', 'a', validity='a', hidden=True, readonly=True, desc='bla')
        self.assertEqual(e, c.e)

    def test_add(self):

        with configuration.create() as ONE:
            ONE.a = 11
            ONE.b.c = Property('b.c', 13, 'int', '\d+', False, False, 'blabla')
            ONE.ron = Property('ron', readonly=True)

        with configuration.create() as TWO:
            TWO.b = 13
            TWO.b.c = 17

        with configuration.create() as THREE:
            THREE.ron = 45

        with configuration.create() as ONE_TWO:
            ONE_TWO.a = 11
            ONE_TWO.b = 13
            ONE_TWO.b.c = Property('b.c', 17, 'int', '\d+', desc='blabla')
            ONE_TWO.ron = Property('ron', readonly=True)

        with configuration.create() as TWO_THREE:
            TWO_THREE.b = 13
            TWO_THREE.b.c = 17
            TWO_THREE.ron = 45

        _assertConfigEqual(ONE_TWO, ONE + TWO)

        _assertConfigEqual(TWO_THREE, TWO + Property('ron', 45))

        with self.assertRaises(TypeError):
            ONE + 3

        with self.assertRaises(ConfigError):
            ONE + Configuration('different name')

        with self.assertRaises(ConfigError):
            ONE + THREE


    def test_equal(self):

        self.assertEqual(Configuration(), Configuration())
        self.assertNotEqual(Configuration(), None)

        self.assertNotEqual(Configuration(), Configuration('a_name'))
        self.assertNotEqual(Configuration(), Configuration(value=1))
        self.assertNotEqual(Configuration(), Configuration(type='int'))
        self.assertNotEqual(Configuration(), Configuration(validity='.*'))
        self.assertNotEqual(Configuration(), Configuration(readonly=True))
        self.assertNotEqual(Configuration(), Configuration(hidden=True))
        self.assertNotEqual(Configuration(), Configuration(desc='to rule them all'))

        with configuration.create() as c:
            c.a = 13

        self.assertNotEqual(Configuration(), c)

        with configuration.modify(c):
            c.d.e = Property('d.e', 1, type='int', validity='1', hidden=True, desc='ONE')

        self.assertEqual(c, c + c)

    def test_file_functions(self):
        import tempfile
        tf = tempfile.NamedTemporaryFile()
        cfg = configuration.from_defaults()

        configuration.write_to_file(cfg, tf.name)

        # compare with the limited cfg the configparser can return
        parsed = configuration.from_configparser(tf.name)
        assert len(cfg) == len(parsed), '%r <--> %r' % (cfg, parsed)
        for key in cfg:
            this, that = cfg[key], parsed[key]
            assert Key(this.name) == Key(that.name)
            assert str(this.value) == str(that.value)
        assert len(cfg) == len(parsed), 'no properties must be added while comparing: %r <--> %r' % (this, that)


def _assertPropertyEqual(this, that):
    assert Key(this.name) == Key(that.name)
    assert this.value == that.value, '%s: %r != %r' % (this.name, this.value, that.value)
    assert this.type == that.type
    assert this.validity == that.validity
    assert this.readonly == that.readonly, '%s: %s != %s' % (this.name, this.readonly, that.readonly)
    assert this.hidden == that.hidden, '%s: %s != %s' % (this.name, this.hidden, that.hidden)
    assert this.desc == that.desc


def _assertConfigEqual(this, that):
    assert len(this) == len(that), '%r <--> %r' % (this, that)
    for key in this:
        _assertPropertyEqual(this[key], that[key])
    assert len(this) == len(that), 'no properties must be added while comparing: %r <--> %r' % (this, that)

if __name__ == "__main__":
    unittest.main()
