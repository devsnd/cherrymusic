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

import os
import re

from collections import MutableMapping, OrderedDict

from cherrymusicserver import log
from cherrymusicserver import util


def from_defaults():
    '''load default configuration. must work if path to standard config file is unknown.'''
    c = Configuration()

    mediabasedir = os.path.join(os.path.expanduser('~'), 'Music')
    c._set('media.basedir', mediabasedir, warn_on_create=False)
    c.media.basedir._desc = """
                            BASEDIR specifies where the media that should be
                            served is located. It must be the absolute path, e.g.
                            BASEDIR=/absolute/path/to/media.
                            
                            Links: If your operating system supports them,
                            you can use symlinks directly in BASEDIR. Links to
                            directories which contain BASEDIR will be ignored,
                            just like all links not directly in, but in sublevels
                            of BASEDIR. This is to guard against the adverse
                            effects of link cycles. 
                            """

    c.media.playable = 'mp3 m4a m4v ogv oga wav webm'
    c.media.playable._desc = """
                                PLAYABLE is a space-separated list of media file
                                extensions that can be played by jPlayer.
                                """

    c.media.transcode = False
    c.media.transcode._desc = """
                                TRANSCODE (experimental!) enables automatic live transcoding 
                                of the media to be able to listen to every format on every device.
                                This requires you to have the appropriate codecs installed.
                                Please note that transcoding will significantly increase the stress on the CPU!
                                """
    c.media.fetch_album_art = False
    c.media.fetch_album_art = """
                                Tries to fetch the album cover from various locations in the web.
                                They will be shown next to folders that qualify as a possible
                                album.
                                """

    c._set('search.maxresults', 20, warn_on_create=False)
    c.search.maxresults._desc = """
                                MAXRESULTS sets the maximum amount of search results
                                to be displayed. If MAXRESULTS is set to a higher value,
                                the search will take longer, but will also be more accurate.
                            
                                """


    c._set('look.theme', 'zeropointtwo', warn_on_create=False)
    c.look.theme._desc = """
                        Available themes are: "zeropointtwo", "hax1337".
                        To create your own theme, you can simply copy the theme
                        to ~/.cherrymusic/themes/yournewtheme and modify it to
                        your will. Then you can set theme=yournewtheme
                        """

    c._set('browser.maxshowfiles', '100', False)
    c.browser.maxshowfiles._desc = '''
                                    MAXSHOWFILES specifies how many files and folders should
                                    be shown at the same time. E.g. if you open a folder
                                    with more than MAXSHOWFILES, the files will be grouped 
                                    according to the first letter in their name.
                                    100 is a good value, as a cd can have up to 99 tracks.
                                    '''

    c._set('server.port', '8080', False)
    c.server.port._desc = 'The port the server will listen to.'


    c.server.logfile = 'site.log'
    c.server.logfile._desc = 'the logfile in which server errors will be logged'

    c.server.localhost_only = 'False'
    c.server.localhost_only._desc = '''
                                    when localhost_only is set to true, the server will not
                                    be visible in the network and only play music on the
                                    same computer it is running on
                                    '''

    c.server.localhost_auto_login = 'False'
    c.server.localhost_auto_login._desc = '''
                                    When localhost_auto_login is set to "True", the server will
                                    not ask for credentials when using it locally. The user will
                                    be automatically logged in as admin.
                                    '''

    c.server.enable_ssl = 'False'
    c.server.enable_ssl._desc = '''
                                The following options allow you to use cherrymusic with
                                https encryption. You must have "pyOpenSSL" installed to
                                be able to use it. If enable_ssl is set to False, all other
                                ssl options will be ommited.
                                '''

    c.server.ssl_port = '8443'
    c.server.ssl_port._desc = '''
                                The port that will listen to SSL encrypted requests. If
                                use_ssl is set to True, all unencrypted HTTP requests
                                will be redirected to this port.
                                '''

    c.server.ssl_certificate = 'certs/server.crt'
    c.server.ssl_private_key = 'certs/server.key'

    return c


def from_configparser(filepath):
    """Have an ini file that the python configparser can understand? Pass the filepath
    to this function, and a matching Configuration will magically be returned."""

    if not os.path.exists(filepath):
        log.e('configuration file not found: %s', filepath)
        return None
    if not os.path.isfile(filepath):
        log.e('configuration path is not a file: %s', filepath)
        return None

    from configparser import ConfigParser
    cfgp = ConfigParser()
    cfgp.read(filepath)
    dic = {}
    try:
        for section_name, section in cfgp.items():
            dic[section_name] = dict([i for i in section.items()])
    except TypeError:
        #workaround for python3.1, can be dropped when debian is ready..
        for section_name in cfgp.sections():
            dic[section_name] = {}
            for name, value in cfgp.items(section_name):
                 dic[section_name][name] = value
        #workaround end
                     
    #check config file has missing keys
    containedNewKey = False
    defaults = from_defaults()
    for prop in sorted(defaults.list, key=lambda p: p[0]):
            fullname, value, desc = prop
            if Property._namesep in fullname:
                section, subkey = fullname.split(Property._namesep, 1)
            else:
                section, subkey = ('', fullname)
            if not section in dic:
                log.i('Section %s not in configuration. Using default values for whole section.' % (section))
            elif subkey and not subkey in dic[section]:
                log.i('Missing key "%s" in configuration. Using default value.' % (fullname))
    return Configuration(dic=dic)


def write_to_file(cfg, filepath):
    """Write a configuration to the given file so that its readable by configparser"""
    with open(filepath, mode='w', encoding='utf-8') as f:

        def printf(s):
            f.write(s + os.linesep)

        lastsection = None
        for prop in sorted(cfg.list, key=lambda p: p[0]):
            fullname, value, desc = prop
            if Property._namesep in fullname:
                section, subkey = fullname.split(Property._namesep, 1)
            else:
                section, subkey = ('', fullname)
            if section != lastsection:
                lastsection = section
                printf('%s[%s]' % (os.linesep, section,))
            if desc:
                printf('')
                lines = util.phrase_to_lines(desc)
                for line in lines:
                    printf('; %s' % (line,))
            printf('%s = %s' % (subkey, value))


def from_dict(d):
    if not isinstance(d, dict):
        raise TypeError("'d' must be a dict, is: %s %s" % (type(d), repr(d)))
    root = Configuration()
    for key, value in d.items():
        root[key] = value
    return root


class ConfigError(Exception):
    pass

class Key(object):

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
    __reserved_names = ['name', 'value', 'valtype', 'desc', 'readonly', 'hidden', 'validity', ]

    @classmethod
    def reserved(cls):
        try:
            return cls.__reserved
        except AttributeError:
            res = [cls._normalize(o.__name__) for o in cls.__reserved_objects]
            res += cls.__reserved_names
            cls.__reserved = res
            return res

    @classmethod
    def _validate_localkey(cls, key):
        if not (key and type(key) == str and cls._name_patn.match(key)):
            raise ConfigError("invalid property name: '%s': a name must be a non-empty string, only contain the characters '%s' and not begin with '%s'"
                           % (key, cls._namechars, cls._name_nonleadchars))
        cls._validate_no_keyword(key)

    @classmethod
    def _validate_complexkey(cls, key):
        if not (key and type(key) == type('') and cls._qual_name_patn.match(key)):
            raise ConfigError("invalid property name: '%s': names must be non-empty strings, only consist of the characters: '%s' and be separated by a '%s'"
                           % (key, cls._namechars, cls._namesep))
        cls._validate_no_keyword(key)

    @classmethod
    def _validate_no_keyword(cls, key):
        reserved = cls.reserved()
        if cls._normalize(key) in reserved:
            raise ConfigError("invalid name: '%s' is in reserved words: %s" % (key, str(reserved)))

    @classmethod
    def _normalize(cls, key):
        return key.lower()

    def __init__(self, name):
        if name is None:
            name = ''
        elif name:
            self._validate_complexkey(name)
        self._fullname = name

    def __repr__(self):
        return self._fullname

    __str__ = __repr__

    def __len__(self):
        return len(self._fullname)

    def __add__(self, name):
        if isinstance(name, Key):
            name = name._fullname
        if self._fullname and name:
            return Key(self._namesep.join((self._fullname, name)))
        return Key(name + self._fullname)

    @property
    def str(self):
        return self.__str__()

    @property
    def normstr(self):
        return self._normalize(self._fullname)

    @property
    def split(self):
        head, _, tail = self._fullname.partition(self._namesep)
        return Key(head), Key(tail)

    @property
    def head(self):
        return self.split[0]

    @property
    def tail(self):
        return self.split[1]

    @property
    def last(self):
        try:
            return Key(self._fullname.split(self._namesep)[-1])
        except IndexError:
            raise ConfigError('key is empty')



class Property(object):

    DEFAULTS = dict.fromkeys(('name', 'value', 'valtype', 'readonly', 'hidden', 'validity', 'desc'))

    def __init__(self, name, value=None, valtype=None, readonly=None, hidden=None, validity=None, desc=None):
        if not name:
            raise ValueError("'name' must not be None or empty")
        Key(name)
        self._name = name
        self._type = valtype
        self._value = None
        self._converter = ValueConverter(value)
        self.validity = validity
        self.readonly = readonly
        self.hidden = hidden
        self.value = value
        self.desc = desc


    def __getitem__(self, name):
        return self.__getattribute__(name)

    def __setitem__(self, name, value):
        if name not in Key.reserved():
            raise ConfigError("can't set item '%s': item does not exist" % name)
        self.__setattr__(name, value)

    def __bool__(self):
        return self.bool

    def __int__(self):
        return self.int

    def __float__(self):
        return self.float

    def __repr__(self):
        return str((self.name, self.value, self.desc))

    def __str__(self):
        return self.str

    @property
    def name(self):
        return self._name

    @property
    def valtype(self):
        return self._type

    @property
    def dict(self):
        d = {}
        for key in self.DEFAULTS:
            actual = self[key]
            if actual:
                d[key] = actual
        return d

    @property
    def list(self):
        return self._converter['list']

    @property
    def int(self):
        return self._converter['int']

    @property
    def float(self):
        return self._converter['float']

    @property
    def bool(self):
        return self._converter['bool']

    @property
    def str(self):
        return self._converter['str']

    @util.Property
    def value():
        def fget(self):
            return self._converter[self.type] if self.valtype else self._value

        def fset(self, value):
            if self.readonly:
                raise ConfigError('cannot change value: %s is readonly' % self.name)
            if not (value is None or self._value is None or isinstance(value, type(self._value))):
                raise TypeError()
            if not self._isvalid(value):
                raise ValueError('cannot set value of %s: %s is invalid' % (self.name, value))
            self._value = value
            self._converter.value = value

        return locals()

    @util.Property
    def desc():
        def fget(self):
            return self.__desc

        def fset(self, desc):
            self.__desc = '' if desc is None else desc

        def fdel(self):
            self.__desc = ''

        return locals()

    def _isvalid(self, value):
        return True     #TODO


class Configuration(Property):


    def __init__(self, name=None, parent=None):
        assert name or not parent
        super().__init__(name if name else 'root')
        self._name = name
        self._parent = parent
        self._properties = OrderedDict()


    @property
    def dict(self):
        view = {} if self._isroot() else super().dict
        if 'name' in view:
            del view['name']
        for prop in self._properties.values():
            dic = prop.dict
            if len(dic) == 1 and 'value' in dic:
                value = dic['value']
            else:
                value = dic
            view[Key(prop.name).last.str] = value
        return view


    @property
    def list(self, sort=True):
        view = []
        if (self._value is not None) or self.desc:
            view.append((self.name, self.value, self.desc))
        for p in self._properties.values():
            view += p.list
        return view


    @property
    def name(self):
        return self._key.str


    @property
    def _key(self):
        return self._getfullkey()

    def _getfullkey(self, accu=''):
        accu = Key(self._name) + accu
        if self._parent is None:
            return accu
        return self._parent._getfullkey(accu)


    @util.Property
    def readonly():
        def fget(self):
            if self._readonly is None and not self._isroot():
                return self._parent.readonly
            return self._readonly

        def fset(self, value):
            self._readonly = True if value else False

        def fdel(self):
            self._readonly = None

        return locals()


    @util.Property
    def hidden():
        def fget(self):
            if self._hidden is None and not self._isroot():
                return self._parent.hidden
            return self._hidden

        def fset(self, value):
            self._hidden = True if value else False

        def fdel(self):
            self._hidden = None

        return locals()


    def __bool__(self):
        return bool(self._properties)


    def __repr__(self):
        name = self.name
        if self._isroot():
            name = "(root)"
        return '[%s %s]' % (self.__class__.__name__, name)


    def __getitem__(self, name):
        try:
            return self._get(Key(name))
        except ConfigError:
            return super().__getitem__(name)


    def __setitem__(self, name, value):
        try:
            return self._set(Key(name), value)
        except ConfigError:
            return super().__setitem__(name, value)


    def __delitem__(self, name):
        self._del(Key(name))


    def __getattr__(self, name):
        if name.startswith('_') or name in Key.reserved():
            return super().__getattribute__(name)
        return self._get_local(Key(name))


    def __setattr__(self, name, value):
        if name.startswith('_') or name in Key.reserved():
            return super().__setattr__(name, value)
        self._set_local(Key(name), value)


    def __delattr__(self, name):
        if name.startswith('_') or name in Key.reserved():
            return super().__delattr__(name)
        self._del_local(Key(name))


    def _isroot(self):
        return self._parent is None


    def _create_child(self, name):
        child = Configuration(name, parent=self)
        self._properties[Key(name).normstr] = child
        return child


    def _merge(self, other):
        if isinstance(other, Configuration) or isinstance(other, Property):
            other = other.dict
        if not isinstance(other, dict):
            self.value = other
        else:
            for key, value in other.items():
                self[key] = value


    def _get(self, key):
        head, tail = key.split
        local = self._get_local(head)
        return local[tail.str] if tail else local


    def _get_local(self, key, warn_on_create=True):
        try:
            value = self._properties[key.last.normstr]
            return value
        except KeyError:
            return self._create_child(key.last.str)


    def _set(self, key, value, warn_on_create=True):
        head, tail = key.split
        if tail:
            local = self._get_local(head)
            local[tail.str] = value
        else:
            self._set_local(head, value)


    def _set_local(self, key, value):
        local = self._get_local(key)
        local._merge(value)


    def _del(self, key):
        head, tail = key.split
        if tail:
            self._get_local(head)._del(tail)
        self._del_local(head)


    def _del_local(self, key):
        try:
            del self._properties[key.last.normstr]
        except KeyError:
            log.w('trying to delete non-existent property %s%s', (self._getfullkey() + key.last).str)


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
        val = val.replace('_', ' ')
        return re.findall(r'\w+', val)
    if isinstance(val, (list, tuple, set)):
        return list(val)
    else:
        raise TransformError('list', val, default=[])

@transformer('int')
def _to_int_transformer(val=None):

    def ishex(s):
        return re.match(r'[+-]?0(x|X)[0-9a-fA-F]+$', s)

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
        self.value = val


    def __getitem__(self, tname):
        t = self.__transformers[tname]
        try:
            return t(self.value)
        except TransformError as e:
            log.w('%s; returning default value of %s', e.msg, str(e.suggested_default))
            return e.suggested_default

    def __contains__(self, name):
        return name in self.__transformers.keys()
