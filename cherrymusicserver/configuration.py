#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2016 Tom Wallroth & Tilman Boerner
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

#python 2.6+ backward compability
from __future__ import unicode_literals
from io import open

import itertools
import os
import re
import weakref

from collections import Mapping, namedtuple
from backport.collections import OrderedDict
from backport import callable

from cherrymusicserver import util
from cherrymusicserver import log as logging


def _validate_basedir(basedir):
    if not basedir:
        raise ValueError('basedir must be set')
    if not os.path.isabs(basedir):
        raise ValueError('basedir must be absolute path: {basedir}'.format(basedir=basedir))
    if not os.path.exists(basedir):
        raise ValueError("basedir must exist: {basedir}".format(basedir=basedir))
    if not os.path.isdir(basedir):
        raise ValueError("basedir must be a directory: {basedir}".format(basedir=basedir))
    return True


def from_defaults():
    '''load default configuration. must work if path to standard config file is unknown.'''

    c = ConfigBuilder()

    with c['media.basedir'] as basedir:
        basedir.value = None
        basedir.valid = _validate_basedir
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        basedir.doc = _("""
                    BASEDIR specifies where the media that should be
                    served is located. It must be an absolute path, e.g.
                    BASEDIR=/absolute/path/to/media.

                    Links: If your operating system supports them,
                    you can use symlinks directly in BASEDIR. Links to
                    directories which contain BASEDIR will be ignored,
                    just like all links not directly in, but in sublevels
                    of BASEDIR. This is to guard against the adverse
                    effects of link cycles.
                            """)

    with c['media.transcode'] as transcode:
        transcode.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        transcode.doc = _("""
                    TRANSCODE (experimental!) enables automatic live transcoding
                    of the media to be able to listen to every format on every device.
                    This requires you to have the appropriate codecs installed.
                    Please note that transcoding will significantly increase the stress on the CPU!
                            """)

    with c['media.fetch_album_art'] as fetch:
        fetch.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        fetch.doc = _("""
                    Tries to fetch the album cover from various locations in the web,
                    if no image is found locally. By default it will be fetched from amazon.
                    They will be shown next to folders that qualify as a possible
                    album.
                            """)

    with c['media.show_subfolder_count'] as subfoldercount:
        subfoldercount.value = True
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        subfoldercount.doc = _("""
                    Show the number of sub-folders and tracks contained
                    in any folder. This will increase the stress for the
                    server, so if you're running CherryMusic on a 386DX II
                    or similar, it is recommended to deactivate this feature.
                            """)


    with c['media.maximum_download_size'] as maxdl:
        maxdl.value = 1024*1024*250
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        maxdl.doc = _("""
                    Maximum size in bytes of all files to be downloaded in one zipfile.
                    Defaults to {default_value} {default_unit}.
                            """.format(default_value='250', default_unit=_('megabytes')))

    with c['search.maxresults'] as maxresults:
        maxresults.value = 20
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        maxresults.doc = _("""
                    MAXRESULTS sets the maximum amount of search results
                    to be displayed. If MAXRESULTS is set to a higher value,
                    the search will take longer, but will also be more accurate.
                            """)

    with c['search.load_file_db_into_memory'] as memory:
        memory.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        memory.doc = _("""
                    This will load parts of the database into memory for improved
                    performance. This option should only be used on systems with
                    sufficient memory, because it will hurt the performance otherwise.
                            """)

    with c['browser.maxshowfiles'] as maxshowfiles:
        maxshowfiles.value = 100
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        maxshowfiles.doc = _('''
                    MAXSHOWFILES specifies how many files and folders should
                    be shown at the same time. E.g. if you open a folder
                    with more than MAXSHOWFILES, the files will be grouped
                    according to the first letter in their name.
                    100 is a good value, as a CD can have up to 99 tracks.
                            ''')

    with c['browser.pure_database_lookup'] as pure_database_lookup:
        pure_database_lookup.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        pure_database_lookup.doc = _("""
                    Only use the media database, never the filesystem, for content
                    lookups in browser and search. Useful if the media files reside
                    on an external hard drive or behind a slow network connection.
                            """)

    with c['server.port'] as port:
        port.value = 8080
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        port.doc = _('The port the server will listen to.')

    with c['server.ipv6_enabled'] as ipv6:
        ipv6.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        ipv6.doc = _("""When set to true, the server will listen on a IPv6
                          socket instead of IPv4""")

    with c['server.localhost_only'] as localhost_only:
        localhost_only.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        localhost_only.doc = _('''
                    When localhost_only is set to true, the server will not
                    be visible in the network and only play music on the
                    same computer it is running on.

                    Activating this option binds the server to IP 127.0.0.1 or
                    [::1], depending on whether server.ipv6_enabled is true.
                    The server should also be reachable as "localhost" in any
                    case.
                            ''')

    with c['server.rootpath'] as rootpath:
        rootpath.value = '/'
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        rootpath.doc = _('''
                    The path cherrymusic will be available on. Normally
                    you'll want to leave it as '/', so that CherryMusic is
                    available under e.g. localhost:8080. You might want to
                    change the path if CherryMusic runs behind a reverse
                    proxy. Changing it to '/cherrymusic' will make it available
                    under e.g. localhost:8080/cherrymusic
                                ''')


    with c['server.localhost_auto_login'] as localhost_auto_login:
        localhost_auto_login.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        localhost_auto_login.doc = _('''
                    When localhost_auto_login is set to "True", the server will
                    not ask for credentials when using it locally. The user will
                    be automatically logged in as admin.
                            ''')

    with c['server.permit_remote_admin_login'] as permit_remote_admin_login:
        permit_remote_admin_login.value = True
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        permit_remote_admin_login.doc = _('''
                    When permit_remote_admin_login is set to "False", admin users
                    may only log in from the computer cherrymusic is currently
                    running on. This can improve security.
                            ''')

    with c['server.keep_session_in_ram'] as keep_session_in_ram:
        keep_session_in_ram.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        keep_session_in_ram.doc = _('''
                    Will keep the user sessions in RAM instead of a file in the
                    configuration directory. This means, that any unsaved
                    playlists will be lost when the server is restarted.
                            ''')

    with c['server.ssl_enabled'] as ssl_enabled:
        ssl_enabled.value = False
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        ssl_enabled.doc = _('''
                    The following options allow you to use cherrymusic with
                    https encryption. If ssl_enabled is set to "False", all other
                    ssl options will be ommited.
                            ''')

    with c['server.ssl_port'] as ssl_port:
        ssl_port.value = 8443
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        ssl_port.doc = _('''
                    The port that will listen to SSL encrypted requests. If
                    ssl_enabled is set to "True", all unencrypted HTTP requests
                    will be redirected to this port.
                            ''')

    with c['server.ssl_certificate'] as ssl_certificate:
        ssl_certificate.value = 'certs/server.crt'
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        ssl_certificate.doc = _('''
                    The SSL certiticate sent to the client to verify the
                    server's authenticity. A relative path is relative to the
                    location of the CherryMusic configuration file.
                            ''')

    with c['server.ssl_private_key'] as ssl_private_key:
        ssl_private_key.value = 'certs/server.key'
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        ssl_private_key.doc = _('''
                    SSL private key file used by the server to decrypt and sign
                    secure communications. Keep this one secret!  A relative
                    path is relative to the location of the CherryMusic
                    configuration file.
                            ''')

    with c['general.update_notification'] as update_notification:
        update_notification.value = True
        # i18n: Don't mind whitespace - string will be re-wrapped automatically. Use blank lines to separate paragraphs.
        update_notification.doc = _('''
                    Notify admins about available security and feature updates.
                            ''')

    return c.to_configuration()


def from_configparser(filepath):
    """Have an ini file that the python configparser can understand? Pass the filepath
    to this function, and a matching Configuration will magically be returned."""

    if not os.path.exists(filepath):
        logging.error(_('configuration file not found: %(filepath)s'), {'filepath':filepath})
        return None
    if not os.path.isfile(filepath):
        logging.error(_('configuration path is not a file: %(filepath)s'), {'filepath':filepath})
        return None

    try:
        from configparser import ConfigParser
    except ImportError:
        from backport.configparser import ConfigParser
    cfgp = ConfigParser()
    with open(filepath, encoding='utf-8') as fp:
        cfgp.readfp(fp)
    dic = OrderedDict()
    for section_name in cfgp.sections():
        if 'DEFAULT' == section_name:
            section_name = ''
        for name, value in cfgp.items(section_name):
            value += ''   # inner workaround for python 2.6+
                              # transforms ascii str to unicode because
                              # of unicode_literals import
            dic[Key(section_name) + name] = value
    return Configuration.from_mapping(dic)


def write_to_file(cfg, filepath):
    """ Write a configuration to the given file so that it's readable by
        configparser.
    """
    with open(filepath, mode='w', encoding='utf-8') as f:

        def printf(s):
            f.write(s + os.linesep)

        lastsection = None
        for prop in cfg.to_properties():
            if prop.hidden:
                continue
            key, value, doc = (Key(prop.key), prop.value, prop.doc)
            section, subkey = str(key.head), str(key.tail)
            if section != lastsection:
                lastsection = section
                printf('%s[%s]' % (os.linesep, section,))
            if doc:
                printf('')
                lines = util.phrase_to_lines(doc)
                for line in lines:
                    printf('; %s' % (line,))
            printf('%s = %s' % (subkey, value))


def from_dict(mapping):
    '''Alias for :meth:`Configuration.from_mapping`.'''
    return Configuration.from_mapping(mapping)


def from_list(properties):
    '''Alias for :meth:`Configuration.from_properties`.'''
    return Configuration.from_properties(properties)


def to_list(cfg):
    '''Alias for :meth:`Configuration.to_properties`.'''
    return cfg.to_properties()


class ConfigError(Exception):
    """Base class for configuration errors."""
    def __init__(self, key, value=None, msg='', detail=''):
        self.key = key
        self.value = value
        self.msg = msg % {'key': key, 'value': value}
        self.detail = detail % {'key': key, 'value': value}
        Exception.__init__(self, self.key, self.value, self.msg, self.detail)

    def __repr__(self):
        return "{cls}: {msg}, key:{key} value:{val}, {detail}".format(
            cls=self.__class__.__name__,
            key=repr(self.key),
            val=repr(self.value),
            msg=self.msg,
            detail=self.detail,
        )

    def __str__(self):
        detail = self.detail.strip() if hasattr(self, 'detail') else ''
        if detail:
            detail = ' ({0})'.format(detail)
        return '{0}: {1}{2}'.format(self.__class__.__name__, self.msg, detail)


class ConfigNamingError(ConfigError):
    """Something is wrong with the name ('Key') of a config Property."""
    def __init__(self, key, detail=''):
        ConfigError.__init__(self, key, None,
                             'invalid key name: %(key)r', detail)


class ConfigKeyError(ConfigError, KeyError):
    """ A config key does not exist. """
    def __init__(self, key, detail=''):
        ConfigError.__init__(self, key, None,
                             'key does not exist: %(key)r', detail)


class ConfigValueError(ConfigError, ValueError):
    """A configuration property does not accept a value."""
    def __init__(self, key, value, detail=''):
        ConfigError.__init__(self, key, value,
                             'invalid value: %(value)r', detail)


class ConfigWriteError(ConfigError):
    """Error while trying to change an existing configuration property."""
    def __init__(self, key, value, detail=''):
        ConfigError.__init__(self, key, value,
                             "can't write to %(key)s", detail)


def raising_error_handler(e):
    "Simply raise the active exception."
    raise


class error_collector(object):
    """ Callable that can be used to collect errors of Configuration operations
        instead of raising them.
    """
    def __init__(self):
        self.errors = []

    def __call__(self, error):
        self.errors.append(error)

    def __len__(self):
        return len(self.errors)

    def __iter__(self):
        return iter(self.errors)


class Key(object):
    """ A hierarchical property name; alphanumerical and caseless.

        Keys parts can contain ASCII letters, digits and `_`; they must start
        with a letter and be separated by a `.`.
    """
    _sep = '.'
    _re = re.compile(r'^({name}({sep}{name})*)?$'.format(
        name=r'[A-Za-z][A-Za-z0-9_]*',
        sep=_sep,
    ))

    def __init__(self, name=None):
        """ name : Key or str
                `None` means ''
        """
        if None is name:
            name = ''
        elif isinstance(name, Key):
            name = name._str
        elif not isinstance(name, (str, type(''))):
            raise ConfigNamingError(name, 'name must be a Key, str or unicode (is {type!r})'.format(type=type(name)))
        elif not self._re.match(name):
            raise ConfigNamingError(
                name, 'Key parts must only contain the characters [A-Za-z0-9_],'
                            ' start with a letter and be separated by a {seperator}'.format(seperator=self._sep))
        name += ''   # inner workaround for python 2.6+
                    # transforms ascii str to unicode because
                    # of unicode_literals import
        self._str = name.lower()

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self._str)

    def __str__(self):
        return self._str

    def __iter__(self):
        """Iterate over hierarchical key parts,"""
        return iter(map(Key, self._str.split(self._sep)))

    def __len__(self):
        """The number of non-empty hierarchical parts in this Key."""
        return self._str.count(self._sep) + 1 if self._str else 0

    def __add__(self, other):
        """Append something that can become a Key to a copy of this Key."""
        other = Key(other)
        if self and other:
            return self._sep.join((self._str, other._str))
        return Key(self or other)

    def __radd__(self, other):
        """Make a Key of the left operand and add a copy of this key to it."""
        return Key(other) + self

    def __hash__(self):
        return hash(self.normal)

    def __eq__(self, other):
        return self.normal == Key(other).normal

    def __ne__(self, other):
        return not (self == other)

    @property
    def parent(self):
        """ This Key without its last hierarchical part; evaluates to `False`
            if there are less than two parts in this Key.
        """
        lastsep = self._str.rfind(self._sep)
        if lastsep >= 0:
            return Key(self._str[:lastsep])
        return Key()

    @property
    def head(self):
        """ The first hierarchical part of this Key."""
        firstsep = self._str.find(self._sep)
        if firstsep >= 0:
            return Key(self._str[:firstsep])
        return self

    @property
    def tail(self):
        """ This key without its last hierarchical part; evaluates to `False`
            if there are less than two parts in this Key.
        """
        firstsep = self._str.find(self._sep)
        if firstsep >= 0:
            return Key(self._str[firstsep + 1:])
        return Key()

    @property
    def normal(self):
        """The normal, hashable form of this Key to compare against."""
        return self._str


class _PropertyMap(Mapping):
    """ A map of keys to corresponding Properties; immutable, but can generate
        updated copies of itself. Certain unset property attributes are
        inherited from the property with the closest parent key. These
        inherited attributes are: ``valid``, ``readonly`` and ``hidden``.

        Uses the Property.replace mechanic to update existing properties.
    """
    def __init__(self, properties=()):
        dic = OrderedDict((p.key, p) for p in properties)
        sortedkeys = sorted(dic, key=lambda k: Key(k).normal)
        inherit = _InheritanceViewer(dic)
        for key in sortedkeys:
            dic[key] = inherit.property_with_inherited_attributes(key)
        self._dic = dic

    def __repr__(self):
        return '{%s}' % (', '.join(
            '%r: %r' % (k, v) for k, v in self._dic.items()))

    def __len__(self):
        return len(self._dic)

    def __contains__(self, key):
        return key in self._dic

    def __iter__(self):
        return iter(self._dic)

    def __getitem__(self, key):
        try:
            return self._dic[key]
        except KeyError:
            raise ConfigKeyError(key)

    def replace(self, properties, on_error):
        def getnew(prop):
            return self[prop.key].replace(**prop.to_dict())
        return self._copy_with_new_properties(getnew, properties, on_error)

    def update(self, properties, on_error):
        def getnew(prop):
            try:
                return self[prop.key].replace(**prop.to_dict())
            except KeyError:
                return prop
        return self._copy_with_new_properties(getnew, properties, on_error)

    def _copy_with_new_properties(self, getnew, properties, on_error):
        newdic = OrderedDict(self._dic)
        for prop in properties:
            try:
                newprop = getnew(prop)
            except ConfigError as error:
                on_error(error)
                continue
            newdic[newprop.key] = newprop
        return self.__class__(newdic.values())


class Property(namedtuple('PropertyTuple', 'key value type valid readonly hidden doc')):
    """ A configuration Property with attributes for key (name), value, type,
        validation and doc(umentation); immutable.

        Use :meth:`replace` to return a new Property with changed attributes.

        Attribute values of `None` are considered *not set*, and are the
        default. They also have a special meaning to :meth:`replace`.

        key : str
            A string that acts as this Property's identifier (name).
        value :
            Anything goes that fits possible type or validity constraints,
            except for `dict`s (and mappings in general); use hierarchical
            keys to express those.
        type :
            The desired value type to auto-cast to; factually a constraint to
            possible values. If `None` or an empty string, the property value
            will remain unchanged.
        valid : str or callable
            A validity constraint on the value, applied after `type`. A
            *callable* value will be called and the result evaluated in
            boolean context, to decide if a value is valid. A *str* value will
            be interpreted as a regular expression which the whole
            ``str()`` form of a value will be matched against.
        readonly : bool
            A readonly property will refuse any :meth"`replace` calls with a
            :class:`ConfigWriteError`.
        hidden : bool
            Just a flag; interpretation is up to the user.
        doc : str
            A documentation string.
    """

    def __new__(cls, key=None, value=None, type=None, valid=None, readonly=None,
                hidden=None, doc=None):
        try:
            key = Key(key).normal
            type = cls._get_valid_type(value, type)
            valid = valid
            value = cls._validate(valid, cls._to_type(type, value), type)
            readonly = readonly
            hidden = hidden
            doc = doc
        except ValueError as e:
            raise ConfigValueError(key, value, detail=str(e))
        return super(cls, cls).__new__(
            cls, key, value, type, valid, readonly, hidden, doc)

    @property
    def _args(self):
        """The arguments needed to create this Property: ``(name, value)*``."""
        for name in ('key', 'value', 'type', 'valid', 'readonly', 'hidden', 'doc'):
            attr = getattr(self, name)
            if attr is not None:
                yield name, attr

    def to_dict(self):
        return dict(self._args)

    def replace(self, **kwargs):
        """ Return a new property as a copy of this property, with attributes
            changed according to `kwargs`.

            Generally, all attributes can be overridden if they are currently
            unset (`None`). An exception is `value`, which will be overridden
            by anything but `None`. Restrictions set by `type` and `valid`
            apply.
        """
        dic = self.to_dict()
        dic.update(kwargs)
        other = Property(**dic)
        if self.key and other.key and self.key != other.key:
            raise ConfigWriteError(self.key, other.key,
                'new key must match old ({newkey!r} != {oldkey!r})'.format(
                newkey=other.key, oldkey=self.key))
        if self.readonly:
            raise ConfigWriteError(self.key, other.value,
                'is readonly ({value!r})'.format(value=self.value))
        return Property(
            key=self.key or other.key,
            value=self._override_self('value', other),
            type=self._override_other('type', other),
            valid=self._override_other('valid', other),
            readonly=self._override_other('readonly', other),
            hidden=self._override_other('hidden', other),
            doc=self._override_other('doc', other),
        )

    def _override_self(self, attrname, other):
        """ Select the value of an attribute from self or another instance,
            with preference to other."""
        return self.__select_with_preference(other, self, attrname)

    def _override_other(self, attrname, other):
        """ Select the value of an attribute from self or another instance,
            with preference to self."""
        return self.__select_with_preference(self, other, attrname)

    @staticmethod
    def __select_with_preference(preferred, alt, attrname):
        """ Select one of the values of an attribute to two objects, preferring
            the first unless it holds `None`.
        """
        preference = getattr(preferred, attrname, None)
        alternative = getattr(alt, attrname, None)
        return alternative if preference is None else preference

    @staticmethod
    def _get_valid_type(value, type_):
        """ Turn the type argument into something useful. """
        if type_ in (None, ''):
            if type(value) in (bool, int, float, str, type('')):
                type_ = type(value)
            else:
                return None
        typestr = type_.__name__ if isinstance(type_, type) else str(type_)
        typestr += ''   # inner workaround for python 2.6+
                        # transforms ascii str to unicode because
                        # of unicode_literals import
        if not typestr in Transformers:
            return None
        return typestr

    @staticmethod
    def _to_type(type_, value):
        if value is None:
            return value
        try:
            return Transformers[type_](value)
        except TransformError:
            raise ValueError('cannot transform value to type %s' % (type_,))

    @classmethod
    def _validate(cls, valid, value, type_):
        if value is None:
            return value
        validator = cls._validator(valid)
        return cls._validate_single_value(validator, value)

    @classmethod
    def _validate_single_value(cls, validator, value):
        if not validator(value):
            raise ValueError(validator.__name__)
        return value

    @classmethod
    def _validator(cls, valid):
        if callable(valid):
            return valid
        if not valid:
            return lambda _: True
        return cls._regexvalidator(valid)

    @staticmethod
    def _regexvalidator(valid):
        def regex_validator(value):
            testvalue = '' if value is None else str(value)
            testvalue += ''  # python2.6 compatibility
            exp = valid.strip().lstrip('^').rstrip('$').strip()
            exp = '^' + exp + '$'
            if not re.match(exp, testvalue):
                raise ValueError('value string must match {0!r}, is {1!r}'.format(exp, testvalue))
            return True
        return regex_validator


class _PropertyModel(object):
    """ Objects whose __dict__ can be used to create a Property from;
        calling it with a ``key`` argument will yield a nested model.
    """

    # as class member to keep children out of instance __dict__s
    _children = weakref.WeakKeyDictionary()

    @staticmethod
    def to_property(model):
        return Property(**model.__dict__)

    @classmethod
    def model_family_to_properties(cls, parent_model):
        return (Property(**m.__dict__) for m in cls._family(parent_model))

    @classmethod
    def _makechild(cls, parent, key):
        child = cls(Key(parent.key) + key)
        cls._children[parent].append(child)
        return child

    @classmethod
    def _family(cls, root):
        yield root
        for child in itertools.chain(*[cls._family(c) for c in cls._children[root]]):
            yield child

    def __init__(self, key=None):
        self._children[self] = []
        self.key = Key(key).normal

    def __getitem__(self, key):
        return self._makechild(self, key)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass


class ConfigBuilder(object):

    def __init__(self):
        self.models = OrderedDict()

    def __getitem__(self, key):
        return self.models.setdefault(key, _PropertyModel(key))

    def properties(self):
        return itertools.chain(
            *(_PropertyModel.model_family_to_properties(m) for m in self.models.values()))

    def to_configuration(self):
        return Configuration.from_properties(self.properties())


class Configuration(Mapping):
    """ A mapping of keys to corresponding values, backed by a collection of
        :class:`Property` objects.

        Immutable; call :meth:`update` or :meth:`replace` with a mapping
        argument to modify a copy of a configuration.

        Unset Property attributes of ``valid``, ``readonly`` and ``hidden``
        are overridden by those of a property with a "parent" key.
    """

    @classmethod
    def from_properties(cls, properties):
        cfg = cls()
        cfg.__propertymap = _PropertyMap(properties)
        return cfg

    def to_properties(self):
        return self.__propertymap.values()

    @classmethod
    def from_mapping(cls, mapping):
        properties = (Property(key, value) for key, value in mapping.items())
        return cls.from_properties(properties)

    def to_nested_dict(self):
        d = {}
        for key, value in self.items():
            target = d
            for part in Key(key):
                target = target.setdefault(str(part), {})
            if value is not None:
                target[''] = self[key]
        for key in self:
            parent = None
            target = d
            for part in Key(key):
                parent = target
                target = target[str(part)]
            if [''] == list(target):
                parent[str(part)] = target.pop('')
        return d

    def __init__(self):
        self.__propertymap = _PropertyMap()

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__,
                                 tuple(self.__propertymap.values()))

    def __contains__(self, key):
        return key in self.__propertymap

    def __len__(self):
        return len(self.__propertymap)

    def __iter__(self):
        return iter(self.__propertymap)

    def __getitem__(self, key):
        return self.property(key).value

    def property(self, key):
        """ Return the property corresponding to the key argument or raise a
            ConfigKeyError.
        """
        return self.__propertymap[key]

    def replace(self, mapping, on_error=raising_error_handler):
        """ Return a copy of this configuration with some values replaced by
            the corresponding values in the mapping argument; adding new keys
            is not allowed.

            Resulting ConfigErrors will be raised or passed to a callable
            error handler, if given.
        """
        return self._mutated_by(mapping, self.__propertymap.replace, on_error)

    def update(self, mapping, on_error=raising_error_handler):
        """ Return a copy of this configuration with some values replaced or
            added corresponding to the values in the mapping argument.

            Resulting ConfigErrors will be raised or passed to a callable
            error handler, if given.
        """
        return self._mutated_by(mapping, self.__propertymap.update, on_error)

    def _mutated_by(self, mapping, mutator, on_error):
        mutated = self.__class__()
        properties = []
        for key, value in mapping.items():
            try:
                properties.append(Property(key, value))
            except ConfigError as e:
                on_error(e)
        mutated.__propertymap = mutator(properties, on_error)
        return mutated


class _InheritanceViewer(object):
    def __init__(self, propertymap):
        self.propertymap = propertymap

    def property_with_inherited_attributes(self, key):
        property = self.propertymap[key]
        model = _PropertyModel()
        model.__dict__.update(property.to_dict())
        self._inherit_attribute_if_not_set('valid', model)
        self._inherit_attribute_if_not_set('readonly', model)
        self._inherit_attribute_if_not_set('hidden', model)
        return _PropertyModel.to_property(model)

    def _inherit_attribute_if_not_set(self, attrname, model):
        if getattr(model, attrname, None) is None:
            key = Key(model.key).parent
            value = None
            while value is None and key:
                try:
                    value = getattr(self.propertymap[key.normal], attrname, None)
                except KeyError:
                    pass
                key = key.parent
            setattr(model, attrname, value)


Transformers = {}


def transformer(name, *more):
    global Transformers  # hell yeah!

    def transformer_decorator(func):
        Transformers[name] = func
        for additional in more:
            Transformers[additional] = func
        return func
    return transformer_decorator


class TransformError(Exception):

    def __init__(self, transformername, val):
        msg = ("Error while trying to parse value with transformer "
               "'%s': %s" % (transformername, val))
        super(self.__class__, self).__init__(msg)


@transformer(None)
def _identity(val=None):
    return val


@transformer(name='bool')
def _to_bool_transformer(val=None):
    if isinstance(val, (bool, int, float, complex, list, set, dict, tuple)):
        return bool(val)
    if isinstance(val, (type(''), str)):
        if val.strip().lower() in ('yes', 'true', 'y', '1'):
            return True
        if val.strip().lower() in ('false', 'no', '', 'n', '0'):
            return False
    raise TransformError('bool', val)


@transformer('int')
def _to_int_transformer(val=None):
    try:
        return int(val)
    except (TypeError, ValueError):
        raise TransformError('int', val)


@transformer('float')
def _to_float_transformer(val=None):
    try:
        return float(val)
    except (TypeError, ValueError):
        raise TransformError('float', val)


@transformer('str', 'unicode')
def _to_str_transformer(val=None):
    if val is None:
        return ''
    if isinstance(val, (str, type(''))):
        return val.strip() + ''  # inner workaround for python 2.6+
    return str(val) + ''         # transforms ascii str to unicode because
                                 # of unicode_literals import
