#!/usr/bin/python3
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2013 Tom Wallroth & Tilman Boerner
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

from backport import callable as _callable
from backport import with_metaclass as _with_metaclass
from backport.collections import OrderedDict as _OrderedDict
from backport.functools import total_ordering as _total_ordering

from threading import Lock as _Lock


def model(cls):
     return _FieldContainer(cls.__name__, (cls, _ModelBase), dict(cls.__dict__))


def field(default=None, *a, **kw):
    return _Field(default, *a, **kw)


@_total_ordering
class _Field(object):

    __instance_count = 0
    __lock = _Lock()

    def __new__(cls, *args, **kwargs):
        instance = super(_Field, cls).__new__(cls)
        instance.__id = _Field.__get_new_id()
        return instance

    @staticmethod
    def __get_new_id():
        with _Field.__lock:
            _Field.__instance_count += 1
            return _Field.__instance_count

    def __init__(self, default=None, name=None):
        self.default = default
        self.name = name

    def __repr__(self):
        return '{cls}(name={name!r}, default={default!r})'.format(
            cls=self.__class__.__name__,
            name=self.name,
            default= self.default,
        )

    def __lt__(self, other):
        if not isinstance(other, _Field):
            return NotImplemented
        return self.__id < other.__id

    def __hash__(self):
        return self.__id

    def __get__(self, container, owner):
        if container is None:
            return self
        value = container.__values.get(self, self.default)
        return value(container) if _callable(value) else value

    def __set__(self, container, value):
        with self.__lock:
            self.__init(container, value)

    @classmethod
    def register_container(cls, container):
        container.__values = {}

    def __init(self, container, value):
        valdict = container.__values
        if self in valdict:
            raise AttributeError("{0!r} already initialized".format(self.name))
        valdict[self] = self.default if value is None else value


class _FieldContainer(type):

    def __new__(metacls, name, bases, clsdict):
        cls = super(_FieldContainer, metacls).__new__(metacls, name, bases, clsdict)
        cls.__new__ = metacls.__new_instance
        metacls.__register_fields(cls, bases, clsdict)
        metacls.__disallow_foreign_overrides(cls)
        return cls

    @classmethod
    def __new_instance(metacls, cls, *a, **kw):
        instance = object.__new__(cls)
        _Field.register_container(instance)
        try:
            metacls.__init_instance_fields(instance, *a, **kw)
        except (KeyError, IndexError) as err:
            msg_key = "{cls}() got unexpected keyword argument(s) {err!s}"
            msg_idx = "{{cls}}() got too many positional arguments (max. {0}): {{err}}".format(len(cls._fields))
            msg = msg_key if isinstance(err, KeyError) else msg_idx
            raise TypeError(msg.format(cls=cls.__name__, err=err))
        return instance

    @classmethod
    def __init_instance_fields(metacls, instance, *args, **kwargs):
        if len(args) > len(instance._fields):
            raise IndexError(args)

        unknown_kwargs = set(kwargs).difference(set(instance._fields))
        if unknown_kwargs:
            raise KeyError(unknown_kwargs)

        values = dict.fromkeys(instance._fields, None)
        values.update(dict(zip(instance._fields, args)))
        values.update(kwargs)
        for name, value in values.items():
            setattr(instance, name, value)

    @classmethod
    def __register_fields(metacls, cls, bases, clsdict):
        base = metacls.__get_basefields(bases)
        own = metacls.__process_newfields(clsdict)
        fields = _OrderedDict((f.name, f) for f in sorted(base) + sorted(own))
        cls._fields = tuple(fields.keys())
        cls.__fields = tuple(fields.values())

    @classmethod
    def __get_basefields(metacls, bases):
        for base in (b for b in bases if isinstance(b, metacls)):
            for field in base.__fields:
                yield field

    @classmethod
    def __process_newfields(metacls, clsdict):
        newfields = [i for i in clsdict.items() if isinstance(i[1], _Field)]
        for name, field in newfields:
            field.name = name
        return [i[1] for i in newfields]

    @classmethod
    def __disallow_foreign_overrides(metacls, cls):
        for name in dir(cls):
            attr = getattr(cls, name, None)
            if name in cls._fields and not isinstance(attr, _Field):
                raise AttributeError(
                    "{0!r} must be instance of {1}, is {2}".format(
                        name, _Field, type(attr)))


class _ModelBase(_with_metaclass(_FieldContainer)):

    _id = field(default=-1)

    @field
    def _type(self):
        return self.__class__.__name__.lower()

    def __repr__(self):
        return repr(self._as_dict())

    def __eq__(self, other):
        if not isinstance(other, (_ModelBase, dict)):
            return NotImplemented
        selfdict = self._as_dict()
        otherdict = other if isinstance(other, dict) else other._as_dict()
        return selfdict == otherdict

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None     # explicitly set to None for python2 compat

    def _as_dict(self):
        return dict((name, getattr(self, name)) for name in self._fields)
