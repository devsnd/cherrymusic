import unittest

from cherrymusic.configuration import Property, Configuration

class TestProperty(unittest.TestCase):

    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_there_are_reserved_words(self):
        self.failUnless(len(Property.reserved()) > 0)


    def test_reserved_attributes_cannot_be_set(self):
        p = Property('test', 1)
        self.assertTrue('int' in Property.reserved(), "precondition")

        with self.assertRaises(KeyError):
            p.int = 9


    def test_nonreserved_attributes_can_be_set(self):
        p = Property('test', 1)
        self.assertFalse('scattermonkey' in Property.reserved(), "precondition")

        p.scattermonkey = 9


    def test_name_must_not_be_reserved(self):
        self.assertTrue('int' in Property.reserved(), "precondition")
        self.assertRaises(KeyError, Property, name='int')


    def test_name_must_not_contain_separator(self):
        self.assertRaises(KeyError, Property, name='Q.Q')


    def test_name_must_not_be_none_or_empty(self):
        self.assertRaises(KeyError, Property, name=None)
        self.assertRaises(KeyError, Property, name='')


    def test_fullname_contains_parent_names(self):
        a = Property('a', None)
        b = Property('b', None, parent=a)
        c = Property('c', None, parent=b)

        self.assertEquals('a.b.c', c.fullname, 'property.fullname must start with parent names')
        self.assertEquals('a', a.fullname, 'when property without parent, there must be no separator in fullname')


    def test_str_must_equal_value_str(self):
        self.assertEquals(str(99), str(Property('test', 99)))


    def test_bool_must_equal_value_bool(self):
        self.assertEquals(bool(99), bool(Property('test', 99)))


    def test_int_must_equal_value_int_or_0(self):
        self.assertEquals(int('99'), int(Property('test', '99')))
        self.assertEquals(0, int(Property('test', 'kumquat')))


    def test_float_must_equal_value_float_or_0(self):
        self.assertEquals(float('99.9'), float(Property('test', '99.9')))
        self.assertEquals(0, float(Property('test', 'kumquat')))


    def test_value_conversions(self):

        def assert_value_conversions(testvalue, expected):
            p = Property('test', testvalue)
            self.assertEqual(expected[''], p.value, 'returned value must be equal to initialized value')
            self.assertEqual(expected['str'], p.str, 'str conversion must return int version of value')
            self.assertEqual(expected['int'], p.int, 'int conversion must return int version of value')
            self.assertEqual(expected['bool'], p.bool, 'bool conversion must return int version of value')
            self.assertEqual(expected['float'], p.float, 'float conversion must return int version of value')

        assert_value_conversions('99', {
                                        '': '99',
                                        'str': '99',
                                        'int': int('99'),
                                        'bool': bool('99'),
                                        'float': float('99'),
                                        })
        assert_value_conversions('scarface', {
                                        '': 'scarface',
                                        'str': 'scarface',
                                        'int': 0,
                                        'bool': bool('scarface'),
                                        'float': float(0),
                                                   })
        assert_value_conversions(None, {
                                        '': None,
                                        'str': '',
                                        'int': 0,
                                        'bool': bool(None),
                                        'float': float(0),
                                        })


class TestConfiguration(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_name_must_be_consistent_with_init(self):
        self.assertEquals('testname', Configuration('testname').name)


if __name__ == "__main__":
    unittest.main()
