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

from backport import callable, with_metaclass
from backport.collections import OrderedDict
from backport.functools import total_ordering

from threading import Lock

@total_ordering
class Field(object):

    __instance_count = 0
    __lock = Lock()

    def __new__(cls, *args, **kwargs):
        instance = super(Field, cls).__new__(cls)
        instance.__id = Field.__get_new_id()
        return instance

    @staticmethod
    def __get_new_id():
        with Field.__lock:
            Field.__instance_count += 1
            return Field.__instance_count

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
        if not isinstance(other, Field):
            return NotImplemented
        return self.__id < other.__id

    def __hash__(self):
        return self.__id

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        value = self.__value_dict(instance).get(self, self.default)
        return value(instance) if callable(value) else value

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute: {0!r}".format(self.name))

    def init(self, owner_instance, value):
        valdict = self.__value_dict(owner_instance)
        if self in valdict:
            raise AttributeError("{0!r} already initialized".format(self.name))
        valdict[self] = self.default if value is None else value

    def __value_dict(self, instance):
        try:
            return instance.__values
        except AttributeError:
            d = instance.__values = {}
            return d


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
        try:
            metacls.__init_instance_fields(instance, *a, **kw)
        except KeyError as err:
            msg = "{cls}() got an unexpected keyword argument {err!s}"
            # msg_idx = "{{cls}}() takes at most {0} positional arguments but {{err!d}} were given".format(len(cls.__fields))
            raise TypeError(msg.format(cls=cls.__name__, err=err))
        return instance

    @classmethod
    def __init_instance_fields(metacls, instance, *args, **kwargs):
        values = dict.fromkeys(instance.__fields, None)
        values.update(dict(zip(instance._fields, args)))
        values.update(kwargs)
        for name, value in values.items():
            field = instance.__fields[name]
            field.init(instance, values[name])

    @classmethod
    def __register_fields(metacls, cls, bases, clsdict):
        base = metacls.__get_basefields(bases)
        own = metacls.__process_newfields(clsdict)
        fields = OrderedDict((f.name, f) for f in sorted(base) + sorted(own))
        cls._fields = tuple(fields)
        cls.__fields = fields

    @classmethod
    def __get_basefields(metacls, bases):
        for base in (b for b in bases if isinstance(b, metacls)):
            for field in base.__fields.values():
                yield field

    @classmethod
    def __process_newfields(metacls, clsdict):
        newfields = (i for i in clsdict.items() if isinstance(i[1], Field))
        for name, field in newfields:
            field.name = name
            yield field

    @classmethod
    def __disallow_foreign_overrides(metacls, cls):
        for name in dir(cls):
            attr = getattr(cls, name, None)
            if name in cls.__fields and not isinstance(attr, Field):
                raise AttributeError(
                    "{attr!r} must be instance of {expect}, is {type}".format(
                        attr=name,
                        expect=Field,
                        type=type(attr),
                        repr=attr,
                ))


class Model(with_metaclass(_FieldContainer)):

    _id = Field(default=-1)

    @Field
    def _type(self):
        return self.__class__.__name__.lower()

    def __repr__(self):
        return repr(self._as_dict())

    def __eq__(self, other):
        if not isinstance(other, (Model, dict)):
            return NotImplemented
        selfdict = self._as_dict()
        otherdict = other if isinstance(other, dict) else other._as_dict()
        return selfdict == otherdict

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None     # explicitly set to None for python2 compat

    def _as_dict(self):
        return dict((name, getattr(self, name)) for name in self._fields)
