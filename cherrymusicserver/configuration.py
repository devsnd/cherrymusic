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

from collections import MutableSet, OrderedDict, namedtuple

from cherrymusicserver import log as logging
from cherrymusicserver import util


def from_defaults():
    '''load default configuration. must work if path to standard config file is unknown.'''
    with create() as c:

        c.media.basedir = os.path.join(os.path.expanduser('~'), 'Music')
        c.media.basedir.desc = """
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
        c.media.playable.desc = """
                                    PLAYABLE is a space-separated list of media file
                                    extensions that can be played by jPlayer.
                                    """

        c.media.transcode = False
        c.media.transcode.desc = """
                                    TRANSCODE (experimental!) enables automatic live transcoding
                                    of the media to be able to listen to every format on every device.
                                    This requires you to have the appropriate codecs installed.
                                    Please note that transcoding will significantly increase the stress on the CPU!
                                    """
        c.media.fetch_album_art = False
        c.media.fetch_album_art.desc = """
                                    Tries to fetch the album cover from various locations in the web,
                                    if no image is found locally. By default it will be fetched from amazon.
                                    They will be shown next to folders that qualify as a possible
                                    album.
                                    """

        c.search.maxresults = 20
        c.search.maxresults.desc = """
                                    MAXRESULTS sets the maximum amount of search results
                                    to be displayed. If MAXRESULTS is set to a higher value,
                                    the search will take longer, but will also be more accurate.

                                    """

        c.search.load_file_db_into_memory = False
        c.search.load_file_db_into_memory.desc = """
                                    This will load parts of the database into memory for improved
                                    performance. This option should only be used on systems with
                                    sufficient memory, because it will hurt the performance otherwise.
                                    """

        c.browser.maxshowfiles = 100
        c.browser.maxshowfiles.desc = '''
                                        MAXSHOWFILES specifies how many files and folders should
                                        be shown at the same time. E.g. if you open a folder
                                        with more than MAXSHOWFILES, the files will be grouped
                                        according to the first letter in their name.
                                        100 is a good value, as a cd can have up to 99 tracks.
                                        '''

        c.browser.pure_database_lookup = False
        c.browser.pure_database_lookup.desc = """
                                            Only use the media database, never the filesystem, for content
                                            lookups in browser and search. Useful if the media files reside
                                            on an external hard drive or behind a slow network connection.
                                            """

        c.server.port = 8080
        c.server.port.desc = 'The port the server will listen to.'


        c.server.localhost_only = False
        c.server.localhost_only.desc = '''
                                        when localhost_only is set to true, the server will not
                                        be visible in the network and only play music on the
                                        same computer it is running on.
                                        '''

        c.server.localhost_auto_login = False
        c.server.localhost_auto_login.desc = '''
                                        When localhost_auto_login is set to "True", the server will
                                        not ask for credentials when using it locally. The user will
                                        be automatically logged in as admin.
                                        '''

        c.server.permit_remote_admin_login = True
        c.server.permit_remote_admin_login.desc = '''
                                        When permit_remote_admin_login is set to "False", admin users
                                        may only log in from the computer cherrymusic is currently
                                        running on. This can improve security.
                                        '''

        c.server.keep_session_in_ram = False
        c.server.keep_session_in_ram.desc = '''
                                        Will keep the user sessions in RAM instead of a file in the
                                        configuration directory. This means, that any unsaved
                                        playlists will be lost when the server is restarted.
                                        '''

        c.server.ssl_enabled = False
        c.server.ssl_enabled.desc = '''
                                    The following options allow you to use cherrymusic with
                                    https encryption. If ssl_enabled is set to False, all other
                                    ssl options will be ommited.
                                    '''

        c.server.ssl_port = 8443
        c.server.ssl_port.desc = '''
                                    The port that will listen to SSL encrypted requests. If
                                    ssl_enabled is set to True, all unencrypted HTTP requests
                                    will be redirected to this port.
                                    '''

        c.server.ssl_certificate = 'certs/server.crt'
        c.server.ssl_private_key = 'certs/server.key'

        c.server.dynamic_dns_address = ''
        c.server.dynamic_dns_address.desc = '''
                                    ex: dynamic_dns_address = http://example.dyndns.com/cm
                                    If you have set up a dyndns/no-ip/etc, you can insert the
                                    address that points to cherrymusic here. This will enable
                                    you to use extra features like the opensearch plugin for
                                    your browser, even when your ip changes frequently.
                                    '''

    return c


def from_configparser(filepath):
    """Have an ini file that the python configparser can understand? Pass the filepath
    to this function, and a matching Configuration will magically be returned."""

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
    try:
        for section_name, section in cfgp.items():
            if section_name == 'DEFAULT':
                section_name = ''
            dic[section_name] = dict([i for i in section.items()])
    except TypeError:
        #workaround for python3.1, can be dropped when debian is ready..
        for section_name in cfgp.sections():
            if section_name == 'DEFAULT':
                section_name = ''
            dic[section_name] = {}
            for name, value in cfgp.items(section_name):
                dic[section_name][name] = value
        #workaround end

    return from_dict(dic)


def write_to_file(cfg, filepath):
    """Write a configuration to the given file so that its readable by configparser"""
    with open(filepath, mode='w', encoding='utf-8') as f:

        def printf(s):
            f.write(s + os.linesep)

        lastsection = None
        for prop in to_list(cfg):
            key, value, desc = (Key(prop.name), prop.value, prop.desc)
            section, subkey = key.head.str, key.tail.str
            if section != lastsection:
                lastsection = section
                printf('%s[%s]' % (os.linesep, section,))
            if desc:
                printf('')
                lines = util.phrase_to_lines(desc)
                for line in lines:
                    printf('; %s' % (line,))
            printf('%s = %s' % (subkey, value))


def from_list(l, name='', rename=None):
    '''Turn a list of tuples into a Configuration. Tuple elements must be the
    constructor arguments in their proper order.

    name: if given, return the corresponding sub-configuration
    rename: if given, change the name of the returned configuration to this value
    '''
    with create() as cfg:
        for proptuple in l:
            if Key(proptuple[0]).normstr.startswith(Key(name).normstr):
                cfg += Property(*proptuple)
    if name and name not in cfg:
        raise ValueError("name not found (%r)" % name)
    wanted = cfg._detach(name) if name else cfg
    if rename is not None:
        wanted._rename(rename)
    return wanted



def from_dict(d):
    '''Parse a dict into a configuration. Keys matching the names of Property
    attributes will be treated as such, other will be taken to refer to
    sub-configurations. Nested dicts will be parsed likewise.'''
    return _config_from_dict(d)


def to_list(cfg):
    '''Turn a Configuration into a list of tuples, each tuple containing
    the attributes of a corresponding configuration Property. Properties witout
    value and descriptions might not be included. Passing a single
    Property as argument will return a list containing one tuple.'''
    if not isinstance(cfg, Property):
        raise TypeError('type(cfg) is not a Property: %s' % (type(cfg),))
    if not isinstance(cfg, Configuration):  # cfg is a plain Property
        return [property_to_tuple(cfg)]
    l = [property_to_tuple(p) for p in cfg._recursive_properties() if p.value != None or p.desc]
    return l


def to_dict(cfg):
    '''Turn a configuration into a dict, with keys for its attributes and
    sub-configurations. Sub-configurations will be included as nested dicts.
    Passing a single Property as argument will return a one-level dict containing
    its attributes. Attributes that have default values or that and can be
    deduced in another way might not be included.'''
    if not isinstance(cfg, Property):
        raise TypeError('type(cfg) is not a Property: %s' % (type(cfg),))
    d = _property_to_dict(cfg)
    if not isinstance(cfg, Configuration):  # cfg is a plain Property
        return d
    if cfg._readonly is None and 'readonly' in d:   # remove attributes only inherited from parent
        del d['readonly']
    if cfg._hidden is None and 'hidden' in d:
        del d['hidden']
    for p in cfg._properties.values():
        child_dict = to_dict(p)
        del child_dict['name']
        d[p._key.last.str] = child_dict['value'] if (['value'] == list(child_dict.keys())) else child_dict
    return d


def property_to_tuple(prop):
    '''Transforms a Property into a namedtuple containing all attributes in
    the order expected by the Property constructor.'''
    args = [prop[a] for a in Property._attributes()]
    return _PropTuple(*args)


def _property_to_dict(prop):
    d = {}
    for key in Property._attributes():
        actual = prop[key]
        if actual or key == 'value' and actual is not None and str(actual).strip():
            d[key] = actual
    return d


def _config_from_dict(d, name=None, parent=None):
    if not isinstance(d, dict):
        raise TypeError("'d' must be a dict, is: %s %r" % (type(d), d))
    name = d.get('name', name)
    with create(name=name, parent=parent) as cfg:
        cfg._update(_property_from_dict(d))
        ron = cfg._readonly
        cfg._readonly = None
        for subname, value in (i for i in d.items() if i[0] not in Property._reserved()):
            if isinstance(value, dict):
                value = _config_from_dict(value, name=subname, parent=cfg)
            cfg[subname]._update(value)
        cfg._readonly = ron
    return cfg


def _property_from_dict(dic):
    '''works for dicts with additional keys'''
    kwargs = Property._default_attributes()
    for arg in kwargs:
        if arg in dic:
            kwargs[arg] = dic[arg]
    try:
        return Property(**kwargs)
    except ValueError:
        raise ConfigError(dic)


class create(object):
    '''context manager that allows creating new Configurations. There will be no
    Errors raised when trying to access unknown Properties.'''
    def __init__(self, name=None, value=None, type=None, validity=None, readonly=None, hidden=None, desc=None, parent=None): #@ReservedAssignment
        self.cfg = Configuration(name, value, type, validity, readonly, hidden, desc, parent)

    def __enter__(self):
        self.cfg._create_mode = True
        return self.cfg

    def __exit__(self, exc_type, exc_value, traceback):
        self.cfg._create_mode = False
        return False


class extend(object):
    '''context manager that allows modifying Configurations. There will be no
    Errors raised when trying to access unknown Properties. This does not override
    type, validation or readonly checks.'''
    def __init__(self, cfg):
        if not isinstance(cfg, Configuration):
            raise TypeError('%s needs to be a Configuration' % cfg)
        self.cfg = cfg

    def __enter__(self):
        self.cfg._create_mode = True
        return self.cfg

    def __exit__(self, exc_type, exc_value, traceback):
        self.cfg._create_mode = False
        return False


class ConfigError(Exception):
    pass


class ConfigKeyError(ConfigError):
    pass


class Key(object):
    '''A hierarchically structured name for something. Letters, numbers and
    the underscore are legal characters; only letters are allowed for the first
    character. Use a '.' to delimit hierarchical components. The empty name is
    allowed. In equality comparisons, case is ignored.'''

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

    @classmethod
    def _validate_localkey(cls, key):
        if not (key and type(key) == str and cls._name_patn.match(key)):
            raise ConfigKeyError("invalid key name: '%s': a name must only contain the characters '%s' and not begin with '%s'"
                           % (key, cls._namechars, cls._name_nonleadchars))

    @classmethod
    def _validate_complexkey(cls, key):
        if not (key and type(key) == type('') and cls._qual_name_patn.match(key)):
            raise ConfigKeyError("invalid key name: '%s': names must only consist of the characters: '%s', not begin with '%s' and be separated by a '%s'"
                           % (key, cls._namechars, cls._name_nonleadchars, cls._namesep))

    @classmethod
    def _normalize(cls, key):
        return key.lower()

    def __init__(self, name=''):
        if isinstance(name, Key):
            name = name._fullname
        elif name is None:
            name = ''
        elif not isinstance(name, str):
            raise TypeError("'name' must be str, is %s (%s)" % (name.__class__.__name__, name))
        elif name:
            self._validate_complexkey(name)
        self._fullname = name

    def __repr__(self):
        return self._fullname

    __str__ = __repr__

    def __bool__(self):
        return bool(self._fullname.replace(self._namesep, ''))

    def __len__(self):
        return self._fullname.count(self._namesep) + 1 if self else 0

    def __iter__(self):
        key = self
        while key.head:
            yield key.head
            key = key.tail

    def __add__(self, key):
        if not isinstance(key, Key):
            key = Key(key)
        if self and key:
            return Key(self._namesep.join((self._fullname, key._fullname)))
        return Key(key._fullname + self._fullname)

    def __radd__(self, name):
        return Key(name).__add__(self)

    def __iadd__(self, name):
        raise NotImplementedError(self.__class__.__name__ + ' is immutable')

    def __eq__(self, other):
        return self.normstr == other.normstr

    def __hash__(self):
        return hash(self.normstr)

    @property
    def str(self):
        '''str representation of the key'''
        return self._fullname

    @property
    def normstr(self):
        '''normalized string representation'''
        return self._normalize(self._fullname)

    @property
    def split(self):
        '''split Key into its first component and in those following'''
        head, _, tail = self._fullname.partition(self._namesep)
        return Key(head), Key(tail)

    @property
    def head(self):
        '''the first component as a Key'''
        return self.split[0]

    @property
    def tail(self):
        '''the Key components following the first one, as a Key'''
        return self.split[1]

    @property
    def first(self):
        '''all key components except the last one, as a Key'''
        return Key(self._fullname.rpartition(self._namesep)[0])

    @property
    def last(self):
        '''the last key component as a Key'''
        return Key(self._fullname.rpartition(self._namesep)[2])


class Property(object):
    '''
    A named value, with some extra attributes. Attributes can also be accessed
    through the [] operator.


    Attributes
    ----------

    **name** (final)

    Naming rules follow those of the Key class, except that the names of
    Property attributes and of some builtin classes cannot be used. Check
    Property._reserved() to see which.

    **value**

    The value of this Property. Setting it is subject to type and validation
    checks as detailed below. A value of *None* is considered not set.

    **type** (final)

    A Property can have a "type", which is a string name; however, if one of the
    "known" types is used (see Transformers), it will be used to check and
    autoconvert any value that is being set, with Exceptions raised on mismatch.

    If no type is set, or if the type is unknown, only values of the same type
    as the current value will be excepted. If there is no value set (= None),
    anything can be set as new value.

    Assigning *None* will always work from a type perspective, but might still
    fail validation checks.

    **validity** (final)

    A 'validity' string can be used as a further method to control which values
    can be set. That string, if non-empty, is taken as a regular expression that
    must match the whole str(ingified) value for the value to be legal. ('^' and
    '$' are implied to enclose the validity string.)

    Whitespace will be stripped from validity string and test value before
    matching. *None* is evaluated as the empty string ''.

    If the type is given as 'list', the value will be converted to a list, and
    the validity string applied to each of its parts.

    **readonly**

    If True, the 'readonly' attribute prevents the changing of value or
    description. A value of *None* is taken to mean this attribute is not set,
    and serves as a non-True default value.

    **hidden**

    The interpretation of the 'hidden' flag is up to the user of the class.  A
    value of *None* is taken to mean this attribute is not set, and serves as a
    non-True default value.

    **desc**

    The description is meant to be a string attribute for explanation and
    documentation. The class may collapse whitespace and redistribute line-
    breaks, but will not otherwise touch this attribute.


    Conversion views on value
    -------------------------

    There are couple of additional attributes that will yield the value
    converted to the appropriate type. These are:

    - int
    - float
    - bool
    - str
    - list

    If conversion fails, a default value will be returned that most closely
    coincides with the concept of "no", "nothing", or "empty" in the respective
    type.

    Since the introduction of the *type* attribute has enabled the auto-
    conversion of a Property's value, these additional attributes have become
    less useful. They might be abandoned in the future.


    Standard functions
    ------------------

    **bool()**

    In a boolean context, a Property is considered True only if it has a *value*
    different from *None*, or if any of its other attributes have been set. This
    does not include *name*, which never influences the boolean interpretation.
    '''

    @classmethod
    def _potential_transform_targets(cls):
        return (int, bool, float, complex, str, bytes, list, set, tuple, dict)

    @classmethod
    def _attributes(cls):
        '''take care that these are the same as the constructor arguments and in right order'''
        return ('name', 'value', 'type', 'validity', 'readonly', 'hidden', 'desc',)

    @classmethod
    def _default_attributes(cls):
        defaults = dict.fromkeys(cls._attributes())    # all values None
        return defaults

    @classmethod
    def _reserved(cls):
        try:
            return cls.__reserved
        except AttributeError:
            res = [Key(o.__name__).normstr for o in cls._potential_transform_targets()]
            res += cls._attributes()
            cls.__reserved = res
            return res


    @classmethod
    def _validate_no_keyword(cls, key):
        reserved = cls._reserved()
        for part in key:
            if part.normstr in reserved:
                raise ConfigKeyError("invalid key name: '%s' contains reserved word: %s" % (key, str(reserved)))


    def __init__(self, name, value=None, type=None, validity=None, readonly=None, hidden=None, desc=None): #@ReservedAssignment
        ''''
        type' and 'validity' apply at once, i.e. value will be checked before set.
        see doc comment of the class for information about the arguments.

        Exceptions raised:
        ConfigKeyError    if name violates naming restrictions
        TypeError         if value is of the wrong type
        ValueError        if value is invalid
        '''
        self.__key = Key(name)
        self._validate_no_keyword(self._key)
        self._type = self._get_valid_type(type)
        self.readonly = None
        self._value = None
        self._validity = validity
        self._converter = ValueConverter(None)
        self.value = value
        self.desc = desc
        self.readonly = readonly
        self.hidden = hidden

    @property
    def _key(self):
        return self.__key

    def __getitem__(self, name):
        try:
            return self.__getattribute__(name)
        except AttributeError:
            raise KeyError("'%s' object has no key '%s'" % (self.__class__.__name__, name))


    def __setitem__(self, name, value):
        if name not in self._reserved():
            raise KeyError("'%s' object has no key '%s'" % (self.__class__.__name__, name))
        self.__setattr__(name, value)


    def __delitem__(self, name):
        if name not in self._reserved():
            raise KeyError("'%s' object has no key '%s'" % (self.__class__.__name__, name))
        self.__delattr__(name)


    def __bool__(self):
        return bool(False
                    or self.value is not None
                    or self.type
                    or self.validity
                    or self.readonly is not None
                    or self.hidden is not None
                    or self.desc
                    )


    def __int__(self):
        return self.int


    def __float__(self):
        return self.float


    def __repr__(self):
        return str(_property_to_dict(self))


    def __str__(self):
        return '%(class)s[%(name)s%(value)s%(type)s%(valid)s%(hid)s%(fix)s]' % {
                       'class': self.__class__.__name__,
                       'name': self.name,
                       'value': '' if self.value is None else '=%r' % self.value,
                       'type': ':%s' % self.type if self.type else '',
                       'valid': ':/%s/' % self.validity if self.validity else '',
                       'fix': '(fix)' if self.readonly else '',
                       'hid': '(hid)' if self.hidden else '',
                       }

    def __eq__(self, other):
        if not isinstance(other, Property):
            return False
        if self._key != other._key:
            return False
        if self.type != other.type:
            return False
        if self.validity != other.validity:
            return False
        if self.readonly != other.readonly:
            return False
        if self.hidden != other.hidden:
            return False
        if self.desc != other.desc:
            return False
        if self.value != other.value:
            return False
        return True


    @property
    def name(self):
        return self._key.str


    @property
    def type(self):
        return self._type


    @property
    def validity(self):
        try:
            return self._validity or ''
        except AttributeError:
            return ''


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
    def value(): #@NoSelf
        doc = '''Setting this value is subject to type and validation checks. Deletion
        is equal to setting it to None.

        Exceptions that can be raised:
        ConfigError    if this Property is readonly
        TypeError      if the new value does not match the needed type
        ValueError     if the new value is invalid
        '''
        def fget(self):
            return self._value

        def fset(self, value):
            if self.readonly:
                raise ConfigError('cannot change value: %s %r is readonly'
                                  % (self.__class__.__name__, self.name))
            value = self._to_type(self._validate(value))
            self._value = value
            self._converter.value = value

        def fdel(self):
            self.value = None

        return locals()


    @util.Property
    def desc(): #@NoSelf
        doc = '''raises ConfigError when self.readonly is True'''
        def fget(self):
            return self.__desc

        def fset(self, desc):
            if self.readonly:
                raise ConfigError('cannot change description: %s %r is readonly'
                                  % (self.__class__.__name__, self.name))
            self.__desc = '\n'.join(util.phrase_to_lines('' if desc is None else desc)).strip()

        def fdel(self):
            self.__desc = ''

        return locals()


    def _validate(self, value, validity=None):
        if validity is None:
            validity = self.validity
        if not validity:
            return value
        if self.type != 'list':
            return self._validate_single_value(value, validity)
        else:
            if value is not None:
                try:
                    for v in Transformers['list'](value):
                        self._validate_single_value(v, validity)
                except TransformError:
                    raise ValueError('value cannot be transformed to list: %s' % value)
            return value


    def _validate_single_value(self, value, validity):
        testvalue = '' if value is None else str(value).strip()
        testexpr = validity
        testexpr = testexpr.strip().lstrip('^').rstrip('$').strip()
        testexpr = '^' + testexpr + '$' if testexpr else ''

        if not re.match(testexpr, testvalue):
            raise ValueError("invalid value (%r): doesn't match validity requirement %r"
                             " (testexpr=%r, teststring=%r)"
                             % (value, validity, testexpr, testvalue))

        return value.strip() if isinstance(value, str) else value


    def _to_type(self, value, _type=None):
        if _type is None:
            _type = self.type
        if _type and _type in Transformers:
            value = self._transform(value, _type)
        else:
            value = self._match_existing_type(value)
        return value


    def _match_existing_type(self, value):
        exist = self._value
        ok = value is None or exist is None or isinstance(value, type(exist))
        if not ok:
            value = self._transform(value, type(exist).__name__)
        return value


    def _transform(self, value, typename):
        try:
            return Transformers[typename](value)
        except (TransformError, KeyError) as e:
            if isinstance(e, TransformError):
                if value is None:
                    return e.suggested_default
            elif isinstance(e, KeyError):
                e = 'no transformer for type %s' % e
            raise TypeError("invalid value (%(val)r): is not of required type (%(target)r) and cannot be transformed: %(e)s"
                            % {
                               'val': value,
                               'target': typename,
                               'e': e,
                               })


    def __copy(self):
        return Property(*property_to_tuple(self))

    def __become_like(self, other):
        self._type = other._type or self._type
        self._validity = other._validity or self._validity
        self.desc = other.desc or self.desc
            # use value property to get checks done; do this after type and validity
        self.value = self._value if other._value is None else other.value
        self.hidden = self.hidden if other.hidden is None else other.hidden
            # do this last:
        self.readonly = self.readonly if other.readonly is None else other.readonly

    def _update(self, other):
        '''
        Here's a secret way to change all attributes after construction.
        Pass in another Property of the same name (or with an empty name),
        and all its non-default attributes will be used to overwrite those
        of this Property.

        Type-checking and validation of the value will
        take place after resolving the new type and validity of the Property;
        so changing any of those attributes without the other must be done
        carefully.
        '''
        if self.readonly:
            raise ConfigError('cannot change %s %r: is readonly' % (self.__class__.__name__, self.name,))
        if not isinstance(other, Property):
            self.value = other
            return
        if other.name and Key(self.name) != Key(other.name):
            raise ConfigError('cannot change %s %r: given name differs (%r)'
                              % (self.__class__.__name__, self.name, other.name))

        target = self.__copy()  # ensure atomicity
        try:
            target.__become_like(other)
        except Exception as e:
            raise ConfigError('cannot change %s %r: %s' % (self.__class__.__name__, self.name, e))
        else:
            self.__become_like(other)

    def _get_valid_type(self, value):
        if value in self._potential_transform_targets():
            value = value.__name__
        elif value is None:
            value = ''
        elif not isinstance(value, str):
            raise TypeError("'type' must be None, a str or one of %s" % self._potential_transform_targets())
        if value not in Transformers:
            value = ''
        return value

_PropTuple = namedtuple('PropertyTuple', ' '.join(Property._attributes()))


class PropertySet(MutableSet):
    '''A simple set implementation to keep properties.

    Additional methods get(), modify() and replace(). Operations that need
    only the property name also accept Keys and strings as arguments.

    The set cares only for the Property names, not their other attributes. This
    is especially significant for comparison with other sets and membership
    tests. The only exception to this is the modify method which accesses the
    Property interface and is thus dependent on the state of the modified
    Property.
    '''

    def __init__(self):
        self.__properties = {}

    def __len__(self):
        return len(self.__properties)

    def __contains__(self, item):
        try:
            key = item._key if isinstance(item, Property) else Key(item)
            return key in self.__properties
        except (TypeError, ConfigKeyError):
            return False

    def __iter__(self):
        return (p for p in self.__properties.values())

    def __repr__(self):
        return "PropertySet(%s)" % (', '.join((str(p) for p in self.__properties.values())),)

    def add(self, property):                                #@ReservedAssignment
        self.__check_type(property)
        if property._key not in self.__properties:
            self.__properties[property._key] = property

    def discard(self, item):
        key = item._key if isinstance(item, Property) else Key(item)
        try:
            del self.__properties[key]
        except:
            pass

    def replace(self, property):                            #@ReservedAssignment
        '''Short for discard, followed by add.'''
        self.__check_type(property)
        self.discard(property)
        self.add(property)

    def modify(self, property):                             #@ReservedAssignment
        '''Modify a property to adopt the non-default attributes of the argument.

        Will check for readonly, type and validity. If the property doesn't
        exist, it will be added.
        '''
        self.__check_type(property)
        try:
            self.get(property.name)._update(property)
        except KeyError:
            self.add(property)

    def get(self, item):
        '''Get a property by name or raise a KeyError.'''
        key = item._key if isinstance(item, Property) else Key(item)
        return self.__properties[key]

    def __check_type(self, item):
        if not isinstance(item, Property):
            raise TypeError("'item' must be a Property (%s is a %s)" %
                            (item, type(item).__name__))


class Configuration(Property):
    '''
    A configuration is a *Property* that can have configurations as its children.

    After construction, the name of a Configuration always includes that of its parent.


    Accessing children

        cfg[childname]
        cfg[child.subchild.etc]

        cfg.childname
        cfg.child.subchild.etc

        cfg[''] == cfg

    For non-existing children, **accessing means creating** an empty default,
    which might not stay around after a pure read. (Behavior might change.)


    Assigning to children

        cfg.a = something
        cfg['a'] = something

    If `something` is a Property, its non-default attributes will overwrite
    those of the target. If it is also a *Configuration*, the same principle
    will be applied to their children. If it is neither, `something` will be
    assigned to the value of the target.


    Requirements to merge:

    - the Property to be merged has the same name as the target Property,
    - or an empty name,
    - and the target property is not readonly.

    If a merge fails, a *ConfigError* will be raised, leaving the merge target
    unchanged. However, if a recursive merge fails in the middle, it will simply
    abort, without further cleanup.


    Merging at root level::

        cfgA += propB
        cfgMerged = cfgA + propB

    is equal to::

        cfgA[propB.name] = propB

    Note that in many cases::

         cfgA + cfgB != cfgB + cfgA


    iteration
    ---------

    Iterating over a configuration will yield the names of all its sub-
    configurations, recursively, with the leading name of the parent removed. It
    can be seen as a sequence of all the keys the [] operator will accept,
    except for special ones that refer to the configuration itself or its
    Property attributes.

    length
    ------

    The length of a configuration equals the number of its subconfigurations,
    *recursively*. It is the number of items an iteration will yield.

    operator in
    -----------

    ``a in cfgA`` is True if ``a`` is the *full* name of one of ``cfgA``'s sub-
    properties. Therefore, it coincides only with the names in an iteration of
    ``cfgA``, if ``cfgA`` happens to have an empty name.

    **WARNING:** This behavior is inconsistent with general expectations and
    might change in the future.

    implicit conversion to bool
    ---------------------------

    In a boolean context, a Conversion is considered True only if its *Property*
    nature is True or if it has sub-properties.
    '''

    def __init__(self, name=None,
                 value=None, type=None, validity=None, readonly=None, hidden=None, desc=None, #@ReservedAssignment
                 parent=None):
        self.__key = Key(name)
        self._parent = parent
        super().__init__(name, value, type, validity, readonly, hidden, desc)
        self._properties = OrderedDict()
        self._create = False

    @property
    def _key(self):
        key = self.__key
        if self._parent is not None:
            key = self._parent._key + key
        return key

    def _key_as_seen_from(self, origin):
        if None is origin:
            return self._key
        if self is origin:
            return Key()
        if self._parent is None:
            raise ValueError('%s is no parent of %s' % (origin, self))
        try:
            return self._parent._key_as_seen_from(origin) + self.__key
        except ValueError:
            raise ValueError("%s is no parent of %s" % (origin, self))


    def _recursive_properties(self):
        for p in self._properties.values():
            yield p
            for sub in p._recursive_properties():
                yield sub

    @util.Property
    def _create_mode():     #@NoSelf
        def fget(self):
            try:
                if self._isroot:
                    return self._create
                return self._create or self._parent._create_mode
            except AttributeError:
                return None

        def fset(self, value):
            self._create = True if value else False

        def fdel(self):
            self._create = False

        return locals()



    @property
    def name(self):
        return self._key.str

    @util.Property
    def validity():     #@NoSelf
        def fget(self):
            return super().validity

        def fset(self, newval):
            if self._create_mode:
                self._validate(self.value, '' if newval is None else newval)
                self._validity = newval
            else:
                raise AttributeError("can't set attribute")

        def fdel(self):
            fset(self, None)

        return locals()


    @util.Property
    def type():     #@NoSelf
        def fget(self):
            return super().type

        def fset(self, newval):
            if self._create_mode:
                _type = self._get_valid_type(newval)
                self._to_type(self.value, _type)
                self._type = _type
            else:
                raise AttributeError("can't set attribute")

        def fdel(self):
            fset(self, None)

        return locals()


    @util.Property
    def readonly(): #@NoSelf
        def fget(self):
            try:
                if self._isroot:
                    return self._readonly
                return self._readonly or self._parent.readonly
            except AttributeError:
                return None

        def fset(self, value):
            self._readonly = None if value is None else True if value else False

        def fdel(self):
            self._readonly = None

        return locals()


    @util.Property
    def hidden(): #@NoSelf
        def fget(self):
            try:
                if self._isroot:
                    return self._hidden
                return self._hidden or self._parent.hidden
            except AttributeError:
                return None

        def fset(self, value):
            self._hidden = None if value is None else True if value else False

        def fdel(self):
            self._hidden = None

        return locals()

    def __eq__(self, other):
        if not isinstance(other, Configuration):
            return False
        if not super().__eq__(other):
            return False
        if not len(self) == len(other):
            return False
        for child in self._properties.values():
            if not child._key.last in other:
                return False
            if not child.__eq__(other[child._key.last]):
                return False
        return True


    def __len__(self):
        l = sum((len(p) for p in self._properties.values()))
        return l + len(self._properties)


    def __iter__(self):
        props = self._recursive_properties()
        return (p._key_as_seen_from(self).str for p in props)


    def __contains__(self, name):
        try:
            key = Key(name)
        except ConfigKeyError:
            return False
        props = self._recursive_properties()
        return key.normstr in (p._key_as_seen_from(self).normstr for p in props)


    def __iadd__(self, other):
        if not isinstance(other, Property):
            raise TypeError('parameter must be of a Configuration type (%s is %s)'
                            % (other, type(other)))
        self[other.name] = other
        return self


    def __add__(self, other):
        with create() as merged:
            merged += self
            merged += other
        return merged[self.name]


    def __bool__(self):
        return super().__bool__() or len(self._properties) > 0


    def __repr__(self):
        return repr(to_dict(self))


    def __str__(self):
        sup = super().__str__()
        if len(self):
            sup = sup[:-1] + '(+)]'
        return sup


    def __getitem__(self, name):
        try:
            return self._get(Key(name))
        except ConfigKeyError:  # fallback for when name in self._reserved()
            return super().__getitem__(name)


    def __setitem__(self, name, value):
        try:
            return self._set(Key(name), value)
        except ConfigKeyError:
            return super().__setitem__(name, value)


    def __delitem__(self, name):
        try:
            self._del(Key(name))
        except ConfigKeyError:
            return super().__delitem__(name)


    def __getattr__(self, name):
        if name.startswith('_') or name in self._reserved():
            return super().__getattribute__(name)
        try:
            return self._get_local(Key(name))
        except KeyError:
            raise AttributeError(name)


    def __setattr__(self, name, value):
        if name.startswith('_') or name in self._reserved():
            return super().__setattr__(name, value)
        try:
            self._set_local(Key(name), value)
        except KeyError:
            raise AttributeError(name)


    def __delattr__(self, name):
        if name.startswith('_') or name in self._reserved():
            return super().__delattr__(name)
        self._del_local(Key(name))

    @property
    def _isroot(self):
        return self._parent is None


    def _update(self, other):
        super()._update(other)
        if not isinstance(other, Configuration):
            return
        self.readonly = None    # super()_update might have set readonly to true
        for othersub in other._properties.values():
            ownsub = self._get_local(othersub._key.last)
            ownsub._update(othersub)
        self.readonly = other.readonly  # set readonly last, so sub-updates work


    def _get(self, key):
        head, tail = key.split
        local = self._get_local(head)
        return local[tail.str] if tail else local


    def _get_local(self, key):
        if not key:
            return self
        try:
            return self._properties[key]
        except KeyError:
            if key.normstr in self._reserved():
                raise ConfigKeyError(key.str)
            if self._create_mode:
                return self._properties.setdefault(key, Configuration(key.str, parent=self))
            raise


    def _set(self, key, value):
        head, tail = key.split
        if tail:
            local = self._get_local(head)
            local[tail.str] = value
        else:
            self._set_local(head, value)


    def _set_local(self, key, value):
        local = self._get_local(key)
        local._update(value)


    def _del(self, key):
        head, tail = key.split
        if tail:
            del self._get_local(head)[tail.str]
        else:
            self._del_local(head)


    def _del_local(self, key):
        try:
            del self._properties[key]
        except KeyError:
            if not key:
                logging.warning('trying to delete property from within itself: %s', self.name)
            else:
                logging.warning('trying to delete non-existent property %s', (self._key + key.last).str)


    def _rename(self, newname):
        if not self._isroot:
            raise ConfigError('cannot rename %r: is not a root Configuration' % self.name)
        key = Key(newname)
        self._validate_no_keyword(key)
        self.__key = key


    def _detach(self, name):
        self._validate_no_keyword(Key(name))
        child = self[name]
        del self[name]
        child._parent = None
        return child


Transformers = {}
def transformer(name):
    global Transformers # hell yeah!

    def transformer_decorator(func):
        def transformer_wrapper(self, *args, **kwargs):
            return func(*args, **kwargs)
        ttype = type(name, (object,), {'__new__':transformer_wrapper})
        Transformers[name] = ttype
        return ttype
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
            logging.warning('%s; returning default value of %s', e.msg, str(e.suggested_default))
            return e.suggested_default


    def __contains__(self, name):
        return name in self.__transformers.keys()
