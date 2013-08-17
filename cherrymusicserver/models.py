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


class _ModelMeta(type):

    def __new__(cls, name, bases, clsdict):
        cls.__prohibit_overriding_final_attributes(clsdict)
        cls.__register_fields(bases, clsdict)
        cls.__check_fields(clsdict)
        return super(_ModelMeta, cls).__new__(cls, name, bases, clsdict)

    @classmethod
    def __register_fields(cls, bases, clsdict):
        base = cls.__get_basefields(bases)
        own = cls.__process_newfields(clsdict)
        fields = OrderedDict()
        fields.update(base)
        fields.update(own)
        clsdict['_fields'] = tuple(fields)
        clsdict['__fields'] = fields

    @classmethod
    def __get_basefields(cls, bases):
        basefields = OrderedDict()
        for base in bases:
            basefields.update(getattr(base, '__fields', {}))
        return basefields

    @classmethod
    def __process_newfields(cls, clsdict):
        from operator import itemgetter
        newfields = (i for i in clsdict.items() if isinstance(i[1], Field))
        newfields = sorted(newfields, key=itemgetter(1))
        newfields = OrderedDict(newfields)
        for name in newfields:
            clsdict[name].name = name
        return newfields


    @classmethod
    def __prohibit_overriding_final_attributes(cls, clsdict):
        final = ('_fields',)
        for attr in clsdict:
            if attr in final:
                raise AttributeError('cannot override attribute {0!r}'.format(attr))


    @classmethod
    def __check_fields(cls, clsdict):
        for name in clsdict['_fields']:
            if name in clsdict and not isinstance(clsdict[name], Field):
                raise AttributeError(
                    "{attr!r} must be instance of {expect}, is {type}".format(
                        attr=name,
                        expect=Field,
                        type=type(clsdict[name]),
                ))


class Model(with_metaclass(_ModelMeta)):

    _id = Field(default=-1)

    @Field
    def _type(self):
        return self.__class__.__name__.lower()

    def __new__(cls, *args, **kwargs):
        instance = super(Model, cls).__new__(cls)
        instance.__init_fields(args, kwargs)
        return instance

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

    def __init_fields(self, args, kwargs):
        cls = self.__class__
        values = dict.fromkeys(cls._fields, None)
        values.update(dict(zip(cls._fields, args)))
        values.update(kwargs)
        for name, value in values.items():
            field = getattr(cls, name)
            field.init(self, value)
