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

    c._set('search.maxresults', 20, warn_on_create=False)
    c.search.maxresults._desc = """
                                MAXRESULTS sets the maximum amount of search results
                                to be displayed. If MAXRESULTS is set to a higher value,
                                the search will take longer, but will also be more accurate.
                            
                                """


    c._set('look.theme','zeropointtwo', warn_on_create=False)
    c.look.theme._desc = """
                        Available themes are: "zeropointtwo", "hax1337".
                        To create your own theme, you can simply copy the theme
                        to ~/.cherrymusic/themes/yournewtheme and modify it to
                        your will. Then you can set theme=yournewtheme
                        """

    c._set('browser.maxshowfiles','100',False)
    c.browser.maxshowfiles._desc = '''
                                    MAXSHOWFILES specifies how many files and folders should
                                    be shown at the same time. E.g. if you open a folder
                                    with more than MAXSHOWFILES, the files will be grouped 
                                    according to the first letter in their name.
                                    100 is a good value, as a cd can have up to 99 tracks.
                                    '''

    c._set('server.port','8080',False)
    c.server.port._desc = 'The port the server will listen to.'


    c.server.logfile = 'site.log'
    c.server.logfile._desc = 'the logfile in which server errors will be logged'

    c.server.localhost_only = 'False'
    c.server.localhost_only._desc = '''
                                    when localhost_only is set to true, the server will not
                                    be visible in the network and only play music on the
                                    same computer it is running on
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
    for section_name, section in cfgp.items():
        dic[section_name] = dict([i for i in section.items()])
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
        cls._validate_no_keyword(key)

    @classmethod
    def _validate_no_keyword(cls, key):
        reserved = cls.reserved()
        if cls._normalize(key) in reserved:
            raise KeyError("invalid name: '%s' is in reserved words: %s" % (key, str(reserved)))

    @classmethod
    def _normalize(cls, key):
        return key.lower()

    def __init__(self, name, value=None, parent=None, allow_empty_name=False, desc=None):
        try:
            self. __class__._validate_localkey(name)
        except KeyError as e:
            if not allow_empty_name or name:
                raise e
        self._name = name
        self._value = value
        self._parent = parent
        self.__desc = desc if not desc is None else ''
        self._converter = ValueConverter(value)

    def __setattr__(self, name, value):
        Property._validate_no_keyword(name)
        super().__setattr__(name, value)

    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        if (self._converter._knows(name)):
            return self._converter[name]
        raise AttributeError(self.__class__.__name__ + ' object has no attribute ' + name)

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __bool__(self):
        return self.bool

    def __int__(self):
        return self.int

    def __float__(self):
        return self.float

    def __repr__(self):
        return str((self.fullname, self.value, self._desc))

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

    @util.Property
    def _desc():
        def fget(self):
            return self.__desc

        def fset(self, desc):
            self.__desc = desc

        return locals()


class Configuration(Property):

    @classmethod
    def _make_property(cls, name, value, parent):
        assert not (name is None or parent is None), "name and parent must not be None"
        log.d('make property %s: %s', name, value)
        Configuration._validate_localkey(name)
        if isinstance(value, dict):
            return Configuration(name=name, dic=value, parent=parent)
        return Property(name, value, parent)


    def __init__(self, name=None, dic=None, parent=None, tmp=False):
        super().__init__(name or '', {}, parent, allow_empty_name=parent is None)
        self._tmp = tmp
        self._properties = self._value
        self._converter._transformers['dict'] = lambda v: self.__to_dict()
        self._converter._transformers['list'] = lambda v: self.__to_list(sort=True)
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


    def __to_list(self, sort=True):

        def sort_if_needed(tuples):
            sortkey = lambda t: t.name
            return tuples if not sort else sorted(tuples, key=sortkey, reverse=True)

        view = []
        properties = sort_if_needed(self._properties.values())
        for p in properties:
            if isinstance(p, Configuration):
                view += p.__to_list()
            else:
                view.append((p.fullname, p.value, p._desc))
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
                log.w('config key not found, creating empty property: %s', tmpcfg.fullname)
            else:
                log.d('set config: %s', tmpcfg.fullname)
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
            log.w('trying to delete non-existent property %s%s%s', self.fullname, self._namesep, key)


    def _untemp(self):
        if not self._isroot():
            self.parent._set_local(self.name, self)
            self._tmp = self.parent._tmp
            if self._tmp:
                log.w('config not set: %s', self)
            else:
                log.d('temp config %s attached to %s', self, self.parent.name)


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
        self._val = val
        self._transformers = dict()

    def __getattr__(self, tname):
        return self.__getitem__(tname)

    def __getitem__(self, tname):
        if tname in self._transformers.keys():
            t = self._transformers[tname]
        else:
            t = self.__class__.__transformers[tname]
        try:
            return t(self._val)
        except TransformError as e:
            log.w('%s; returning default value of %s', e.msg, str(e.suggested_default))
            return e.suggested_default

    def _knows(self, name):
        return name in self._transformers.keys() or name in self.__class__.__transformers.keys()
