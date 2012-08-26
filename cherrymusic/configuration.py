import logging
import os
import re


def from_defaults():
    '''load default configuration. must work if path to standard config file is unknown.'''
    c = Configuration()

    c.media.basedir = os.path.join(os.path.expanduser('~'), 'Music')
    c.media.playable = 'mp3 ogg wma flac'

    c.search.cachefile = 'cherry.cache.db'
    c.search.maxresults = '20'

    c.look.theme = 'zeropointtwo'

    c.browser.maxshowfiles = '100'

    c.server.port = '8080'
    c.server.logfile = 'site.log'
    c.server.localhost_only = 'False'

    c.server.use_ssl = 'False'
    c.server.ssl_port = '8443'
    c.server.ssl_certificate = 'certs/server.crt'
    c.server.ssl_private_key = 'certs/server.key'

    return c


def from_configparser(filepath):
    """Have an ini file that the python configparser can understand? Pass the filepath
    to this function, and a matching Configuration will magically be returned."""

    import os
    if not os.path.exists(filepath):
        logging.error('configuration file not found: %s', filepath)
        return None
    if not os.path.isfile(filepath):
        logging.error('configuration path is not a file: %s', filepath)
        return None

    from configparser import ConfigParser
    cfgp = ConfigParser()
    cfgp.read(filepath)
    dic = {}
    for section_name, section in cfgp.items():
        dic[section_name] = dict([i for i in section.items()])
    return Configuration(dic=dic)


class Property(object):

    _name_leadchars = 'a-zA-Z'
    _name_nonleadchars = '0-9_'
    _namechars = _name_leadchars + _name_nonleadchars
    _namesep = '.'
    _name = r'([%s][%s]*)' % (_name_leadchars, _namechars)

    _name_patn = re.compile(r'^%s$' % (_name,))
    _qual_name_patn = re.compile(r'''
                                ^                       # start of string
                                %(name)s                # one name
                                (?: %(sep)s %(name)s )* # more names with leading separators (non-grouping)
                                $                       # nothing else'''
                                % {'name': _name,
                                   'sep': '[' + _namesep + ']'},
                                re.VERBOSE)

    __reserved_objects = [int, bool, float, complex, str, bytes, list, set, tuple, dict]
    __reserved_names = ['name', 'fullname', 'value', 'parent', 'reserved']

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
        if not (key and type(key) == str and cls._name_patn.match(key)):
            raise KeyError("invalid property name: '%s': a name must be a non-empty string, only contain the characters '%s' and not begin with '%s'"
                           % (key, cls._namechars, cls._name_nonleadchars))
        cls._validate_no_keyword(key)

    @classmethod
    def _validate_complexkey(cls, key):
        if not (key and type(key) == type('') and cls._qual_name_patn.match(key)):
            raise KeyError("invalid property name: '%s': names must be non-empty strings, only consist of the characters: '%s' and be separated by a '%s'"
                           % (key, cls._namechars, cls._namesep))
        cls._validate_no_keyword(key);

    @classmethod
    def _validate_no_keyword(cls, key):
        reserved = cls.reserved()
        if cls._normalize(key) in reserved:
            raise KeyError("invalid name: '%s' is in reserved words: %s" % (key, str(reserved)))

    @classmethod
    def _normalize(cls, key):
        return key.lower()

    def __init__(self, name, value=None, parent=None, allow_empty_name=False):
        try:
            __class__._validate_localkey(name)
        except KeyError as e:
            if not allow_empty_name or name:
                raise e
        self._name = name
        self._value = value
        self._parent = parent
        self._converter = ValueConverter(value)

    def __setattr__(self, name, value):
        Property._validate_no_keyword(name)
        super().__setattr__(name, value)

    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        if (self._converter._knows(name)):
            return self._converter[name]
        raise AttributeError(__class__.__name__ + ' object has no attribute ' + name)

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __bool__(self):
        return self.bool

    def __int__(self):
        return self.int

    def __float__(self):
        return self.float

    def __repr__(self):
        return str((self.fullname, self.value))

    def __str__(self):
        return self.str

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
        if not self.parent is None:
            return self.parent._getfullname(accu)
        return accu

    @property
    def value(self):
        return self._value

    @property
    def parent(self):
        return self._parent


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
        super().__init__(name or '', {}, parent, allow_empty_name=parent is None)
        self._tmp = tmp
        self._properties = self._value
        self._converter._transformers['dict'] = self.__to_dict
        self._converter._transformers['list'] = self.__to_list
        if not (dic is None or isinstance(dic, dict)):
            raise ValueError("'dic' parameter must be None or a dict")
        if dic:
            for name, val in dic.items():
                Configuration._validate_complexkey(name)
                self._set(name, val, warn_on_create=False)


    def __to_dict(self):
        view = {}
        for prop in self._properties.values():
            if isinstance(prop, Configuration):
                value = prop.__to_dict()
            else:
                value = prop.value
            view[prop.name] = value
        return view# if not self._name else {self._name: view}


    def __to_list(self, sort=True, parentstr=''):

        def sort_if_needed(tuples):
            sortkey = lambda t: t.name
            return tuples if not sort else sorted(tuples, key=sortkey, reverse=True)

        view = []
        properties = sort_if_needed(self._properties.values())
        for p in properties:
            if isinstance(p, Configuration):
                view += p.__to_list()
            else:
                view.append((p.fullname, p.value))
        return view


    def __bool__(self):
        return bool(self._properties)


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


    def _get_local(self, key, warn_on_create=True):
        try:
            value = self._properties[Configuration._normalize(key)]
            return value
        except KeyError:
            tmpcfg = Configuration(name=key, parent=self, tmp=True)
            if warn_on_create:
                logging.warn('config key not found, creating empty property: %s', tmpcfg.fullname)
            else:
                logging.info('set config: %s', tmpcfg.fullname)
            return tmpcfg


    def _set(self, name, value, warn_on_create=True):
        head, tail = self._splitkey(name)
        if tail:
            return self._get_local(head, warn_on_create)._set(tail, value)
        return self._set_local(name, value)


    def _set_local(self, key, value):
        if not isinstance(value, Configuration):
            value = Configuration._make_property(key, value, parent=self)
        if key:
            self._properties[Configuration._normalize(key)] = value
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
            logging.warn('trying to delete non-existent property %s%s%s', self.fullname, self._namesep, key)
            pass


    def _untemp(self):
        if not self._isroot():
            self.parent._set_local(self.name, self)
            self._tmp = self.parent._tmp
            if self._tmp:
                logging.warn('config not set: %s', self)
            else:
                logging.debug('temp config %s attached to %s', self, self.parent.name)


def transformer(name):
    def transformer_decorator(func):
        def transformer_wrapper(self, *args, **kwargs):
            return func(*args, **kwargs)
        return type(name, (object,), {'__new__': transformer_wrapper})
    return transformer_decorator


class TransformError(Exception):

    def __init__(self, transformername, val, default=None, cause=None):
        self._msg = "Error while trying to parse value with transformer '%s': %s" \
                % (transformername, val)
        self._xform = transformername
        self._value = val
        self._default = default
        self._cause = cause
        super().__init__(self._msg)

    @property
    def msg(self):
        return self._msg

    @property
    def transformer(self):
        return self._xform

    @property
    def badvalue(self):
        return self._value

    @property
    def suggested_default(self):
        return self._default

    @property
    def cause(self):
        return self._cause


@transformer(name='bool')
def _to_bool_transformer(val=None):
    if isinstance(val, (bool, int, float, complex, list, set, dict, tuple)):
        return bool(val)
    try:
        return val.__bool__()
    except AttributeError:
        try:
            return bool(_to_float_transformer(val))
        except (TypeError, ValueError, TransformError):
                if isinstance(val, str) and val.strip().lower() in ('yes', 'true'):
                    return True
                if isinstance(val, str) and val.strip().lower() in ('false', 'no', ''):
                    return False
                raise TransformError('bool', val, default=False)


@transformer('list')
def _to_list_transformer(val=None):
    if isinstance(val, str):
        return re.split(r'\W+', val)
    if isinstance(val, (list, tuple, set)):
        return list(val)
    else:
        raise TransformError('list', val, default=[])

@transformer('int')
def _to_int_transformer(val=None):

    def ishex(s):
        return re.match(r'[+-]?(0(x|X))?[0-9a-fA-F]+$', s) and re.search(r'[a-fA-FxX]', s)

    def isoctal(s):
        return re.match(r'[+-]?0(o|O)[0-7]+$', s)

    try:
        if isinstance(val, str):
            val = val.strip()
            if ishex(val):
                base = 16
            elif isoctal(val):
                base = 8
            else:
                base = 10
            try:
                return int(val, base)
            except ValueError:
                return int(float(val))
        else:
            return int(val)
    except (TypeError, ValueError) as e:
        raise TransformError('int', val, default=int(), cause=e)


@transformer('float')
def _to_float_transformer(val=None):
    '''may call _to_int_transformer'''
    try:
        if isinstance(val, str):
            val = val.strip()
        try:
            return float(val)
        except ValueError:
            try:
                return float(_to_int_transformer(val))
            except TransformError as e:
                raise e.cause if e.cause else ValueError('generic ValueError')
    except (TypeError, ValueError) as e:
        raise TransformError('float', val, default=float(), cause=e)


@transformer('str')
def _to_str_transformer(val=None):
    if val is None:
        return ''
    if isinstance(val, str):
        return val.strip()
    return str(val)



class ValueConverter(object):

    __transformers = { str(t.__name__): t for t in [_to_int_transformer,
                                                    _to_float_transformer,
                                                    _to_bool_transformer,
                                                    _to_list_transformer,
                                                    _to_str_transformer,
                                                    ]}

    def __init__(self, val):
        self._val = val
        self._transformers = dict()

    def __getattr__(self, tname):
        return self.__getitem__(tname)

    def __getitem__(self, tname):
        if tname in self._transformers.keys():
            t = self._transformers[tname]
        else:
            t = __class__.__transformers[tname]
        try:
            return t(self._val)
        except TransformError as e:
            logging.warn('%s; returning default value of %s', e.msg, str(e.suggested_default))
            return e.suggested_default

    def _knows(self, name):
        return name in self._transformers.keys() or name in __class__.__transformers.keys()
