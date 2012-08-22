import re

import logging

logging.basicConfig(level=logging.DEBUG)

class ValueConverter(object):
    transformers = { str(t.__name__): t for t in [int, float, bool, str]}

    @classmethod
    def knows(cls, name):
        return name in ValueConverter.keywords()

    @classmethod
    def keywords(cls):
        return tuple(ValueConverter.transformers.keys())

    def __init__(self, val):
        self._val = val

    def __getattr__(self, tname):
        return self.__getitem__(tname)

    def __getitem__(self, tname):
        t = ValueConverter.transformers[tname]
        try:
            if self._val is None:
                raise ValueError
            return t(self._val)
        except (ValueError, TypeError):
            return t()

class Property(object):

    _name_leadchars = 'a-zA-Z'
    _name_nonleadchars = '0-9_'
    _namechars = _name_leadchars + _name_nonleadchars
    _namesep = '.'

    name_patn = re.compile(r'^[%s][%s]*$' % (_name_leadchars, _namechars))
    qual_name_patn = re.compile(r'''^                   # start of string
                                %(name)s                # one name
                                ( %(sep)s %(name)s )*   # more keys with leading separators
                                $                       # nothing else'''
                                % {'name': '[' + _name_leadchars + '][' + _namechars + ']*',
                                   'sep': '[' + _namesep + ']'},
                                re.VERBOSE)

    __reserved_objects = [int, bool, float, complex, str, bytes, list, set, tuple, dict]
    __reserved_names = ['name', 'fullname', 'value', 'parent']

    @classmethod
    def reserved(cls):
        try:
            return Configuration.__reserved
        except AttributeError:
            res = [Configuration._normalize(o.__name__) for o in cls.__reserved_objects]
            res += cls.__reserved_names
            cls.__reserved = res
            return res

    @classmethod
    def _validate_localkey(cls, key):
        if not (key and type(key) == str and cls.name_patn.match(key)):
            raise KeyError("invalid name: '%s': a local config name must be a non-empty string, only contain the characters '%s' and not begin with '%s'"
                           % (key, cls._namechars, cls._name_nonleadchars))
        cls._validate_no_keyword(key);

    @classmethod
    def _validate_complexkey(cls, key):
        if not (key and type(key) == type('') and cls.qual_name_patn.match(key)):
            raise KeyError("invalid name: '%s': keys must be non-empty strings, only consist of the characters: '%s' and be separated by a '%s'"
                           % (key, cls._namechars, cls._namesep))
        cls._validate_no_keyword(key);

    @classmethod
    def _validate_no_keyword(cls, key):
        reserved = list(ValueConverter.keywords())
        if key.lower() in ValueConverter.keywords():
            raise KeyError("invalid name: '%s' is in reserved words: %s" % (key, str(reserved)))

    @classmethod
    def _normalize(cls, key):
        return key.lower()

    def __init__(self, name, value, parent=None):
        self._name = name if not name is None else ''
        self._value = value
        self._parent = parent
        self._converter = ValueConverter(value)

    def __bool__(self):
        return self.bool

    @property
    def name(self):
        return self._name

    @property
    def fullname(self):
        return self._getfullname()

    def _getfullname(self, accu=''):
        if accu:
            if self.name:
                accu = self.name + Property._namesep + accu
        else:
            accu = self.name
        if self.parent:
            return self.parent._getfullname(accu)
        return accu

    @property
    def value(self):
        return self._value

    @property
    def parent(self):
        return self._parent

    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        if (self._converter.knows(name)):
            return self._converter[name]
        raise AttributeError(__class__.__name__ + ' object has no attribute ' + name)

    def __repr__(self):
        return str((self.fullname, self.value))

    def __str__(self):
        return self.str


class Configuration(Property):

    @classmethod
    def _make_property(cls, name, value, parent):
        assert not (name is None or parent is None), "name and parent must not be None"
        logging.debug('make property %s: %s', name, value)
        Configuration._validate_localkey(name)
        if isinstance(value, dict):
            return Configuration(name=name, dic=value, parent=parent)
        return Property(name, value, parent)

    def __init__(self, name=None, dic=None, parent=None, tmp=False):
        self._parent = parent
        self._tmp = tmp
        self._own_property = None
        self._properties = {}
        super().__init__(name, self._properties, parent)
        if dic:
            for name, value in dic.items():
                Configuration._validate_complexkey(name)
                self._set(name, value)

    def to_dict(self):
        view = {}
        for prop in self._properties.values():
            if isinstance(prop, Configuration):
                value = prop.to_dict()
            else:
                value = prop.value
            view[prop.name] = value
        return view

    def to_list(self, sort=True, parentstr=''):
        def sort_if_needed(tuples):
            sortkey = lambda t: t.name
            return tuples if not sort else sorted(tuples, key=sortkey, reverse=True)
        view = []
        properties = sort_if_needed(self._properties.values())
        for p in properties:
            if isinstance(p, Configuration):
                view += p.to_list()
            else:
                view.append(p)
        return view

    def __bool__(self):
        return bool(self._own_property) or bool(self._properties)

    def __repr__(self):
        name = self.name
        if self._istemp():
            name = "(temp:%s)" % name
        elif self._isroot():
            name = "(root)"
        return '[%s %s]' % (self.__class__.__name__, name)

    def __getitem__(self, name):
        Configuration._validate_complexkey(name)
        return self._get(name)

    def __setitem__(self, name, value):
        Configuration._validate_complexkey(name)
        return self._set(name, value)

    def __delitem__(self, name):
        Configuration._validate_complexkey(name)
        self._del(name)

    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        if name in Property.reserved():
            return super(Configuration, self).__getattr__(name)
        Configuration._validate_localkey(name)
        return self._get_local(name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(Property, self).__setattr__(name, value)
        Configuration._validate_localkey(name)
        self._set_local(name, value)

    def __delattr__(self, name):
        if name.startswith('_'):
            return super(Property, self).__delattr__(name)
        Configuration._validate_localkey(name)
        self._del_local(name)

    def _istemp(self):
        return self._tmp

    def _isroot(self):
        return self.parent is None

    def _splitkey(self, key):
        parts = key.partition(Configuration._namesep)
        return (parts[0], parts[2])

    def _get(self, name):
        head, tail = self._splitkey(name)
        if tail:
            subconf = self._get_local(head)
            return subconf._get(tail)
        return self._get_local(head)

    def _get_local(self, key):
        if not key:
            return self._get_own()
        try:
            value = self._properties[Configuration._normalize(key)]
            return value
        except KeyError:
            return Configuration(name=key, parent=self, tmp=True)

    def _set(self, name, value):
        head, tail = self._splitkey(name)
        if tail:
            return self._get_local(head)._set(tail, value)
        return self._set_local(name, value)

    def _set_local(self, key, value):
        if not isinstance(value, Configuration):
            value = Configuration._make_property(key, value, parent=self)
        if key:
            self._properties[Configuration._normalize(key)] = value
        else:
            self._set_own(value)
        if self._istemp():
            self._untemp()

    def _del(self, name):
        head, tail = self._splitkey(name)
        if tail:
            self._get_local(head)._del(tail)
        self._del_local(head)

    def _del_local(self, key):
        try:
            del self._properties[Configuration._normalize(key)]
        except KeyError:
            pass

    def _get_own(self):
        return self._own_property

    def _set_own(self, value):
        assert isinstance(value, Property) and not isinstance(value, Configuration)
        if self._parent is None:
            raise KeyError("root configurations cannot keep keyless values")
        self._own_property = Configuration._make_property(self._name, value, self._parent)

    def _untemp(self):
        if not self._isroot():
            self.parent._set_local(self.name, self)
            self._tmp = self.parent._tmp
        print('%s untemp %s' % (self.name, 'fail' if self._istemp() else 'ok'))

Config = Configuration()

