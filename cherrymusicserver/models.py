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


def field(default=None, *a, **kw):
    ''' see _Field.__init__'''
    return _Field(default, *a, **kw)


def model(cls):
    ''' Turn a class into a model class that contains some standard fields,
        a dict view, and implements a helpful constructor with optional
        parameters for the model fields.

        >>> # @model             (decorator works, but doctest module is buggy)
        >>> class Foo(object):
        ...     @field
        ...     def x(self): return 'calculated'
        ...
        >>> Foo = model(Foo)                           # workaround for doctest
        >>> Foo().as_dict == {'_id': None, '_type': 'foo', 'x': 'calculated'}
        True

    '''
    name = cls.__name__
    cls.__name__ = name + "_Original"
    return _FieldContainer(name, (cls, _ModelBase), dict(cls.__dict__))


@_total_ordering
class _Field(object):
    ''' The descriptor of a model attribute that's settable exactly once.
        Has a default value, too.

        See :meth:`__init__` for more.
    '''

    __instance_count = 0
    __lock = _Lock()

    def __new__(cls, *args, **kwargs):
        ''' Fields get a private id reflecting the order they are created in'''
        instance = super(_Field, cls).__new__(cls)
        instance.__id = _Field.__get_new_id()
        return instance

    @staticmethod
    def __get_new_id():
        with _Field.__lock:
            _Field.__instance_count += 1
            return _Field.__instance_count

    def __init__(self, default=None, name=None, doc=None):
        ''' Return a model attribute descriptor that's settable exactly once.

            default : value or callable = None
                The default value. Callable values will be called with the
                model object as argument and the result returned.
            name : str = None
                The name of this descriptor. Should equal the name of the
                corresponding attribute.
            doc : str = None
                A documentation string for this model attribute.
        '''
        self.default = default
        self.name = name
        self.doc = doc or (_callable(default) and default.__doc__)

    def __repr__(self):
        return '{cls}(name={name!r}, default={default!r})'.format(
            cls='field' if type(self) is _Field else type(self).__name__,
            name=self.name,
            default= self.default,
        )

    def __lt__(self, other):
        ''' Order fields in the sequence they were created in'''
        if not isinstance(other, _Field):
            return NotImplemented
        return self.__id < other.__id

    def __hash__(self):
        return self.__id

    def __get__(self, container, owner):
        ''' The field value set for the container (model object), or the field
            default value. If that value is callable, it will be called with
            the container as argument, and the result will be returned.
        '''
        if container is None:
            return self
        return self.__value_for(container)

    def __set__(self, container, value):
        ''' The value for a container can be set only once; will raise
            AttributeError on each subsequent call.
        '''
        with self.__lock:
            self.__init(container, value)

    @classmethod
    def register_container(cls, container):
        ''' Make sure the field can access and store its values.'''
        container.__values = {}

    @property
    def doc(self):
        '''Field docstring'''
        return self.__doc__

    @doc.setter
    def doc(self, docstr):
        self.__doc__ = docstr

    def __init(self, container, value):
        valdict = self.__values_for(container)
        if self in valdict:
            raise AttributeError("{0!r} already initialized".format(self.name))
        valdict[self] = value

    @classmethod
    def __values_for(cls, container):
        ''' Store field values inside container object, so they die together
            with it.'''
        return container.__values

    def __value_for(self, container):
        value = self.__values_for(container).get(self, self.default)
        return value(container) if _callable(value) else value

field.__doc__ = _Field.__init__.__doc__


class _FieldContainer(type):
    ''' A metaclass for classes meant to contain registered field attributes.

        Provides:
          - an instance constructor that accepts positional and keyword
            arguments to populate field values,

          - a _field attribute containing the names of contained fields in
            the order they were defined.
    '''

    def __new__(metacls, name, bases, clsdict):
        '''Create a class object, register and check the contained fields.'''
        cls = super(_FieldContainer, metacls).__new__(metacls, name, bases, clsdict)
        cls.__new__ = metacls.__new_instance
        metacls.__register_fields(cls, bases, clsdict)
        metacls.__disallow_foreign_overrides(cls)
        return cls

    @classmethod
    def __new_instance(metacls, cls, *a, **kw):
        ''' __new__(cls, *field_values, **field_value_dict)
        '''
        if len(a) > len(cls._fields):
            raise TypeError(
                '{0}(): too many positional arguments (max. {1}): {2}'.format(
                    cls.__name__, len(cls._fields), a))

        unknown_kwargs = set(kw).difference(set(cls._fields))
        if unknown_kwargs:
            raise TypeError(
                '{0}(): unexpected keyword arguments ({1})'.format(
                    cls.__name__, unknown_kwargs))

        instance = object.__new__(cls)
        _Field.register_container(instance)
        metacls.__init_instance_fields(instance, *a, **kw)
        return instance

    @classmethod
    def __init_instance_fields(metacls, instance, *args, **kwargs):
        values = dict((f.name, f.default) for f in instance.__fields)
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
            if not field.doc:
                field.doc = repr(field)
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
    ''' Base class for model types: can contain fields and provides a dict view
        on them.
    '''

    _id = field()

    @field
    def _type(self):
        ''' the lowercase class name'''
        return self.__class__.__name__.lower()

    def __repr__(self):
        return repr(self.as_dict)

    def __eq__(self, other):
        if not isinstance(other, (_ModelBase, dict)):
            return NotImplemented
        selfdict = self.as_dict
        otherdict = other if isinstance(other, dict) else other.as_dict
        return selfdict == otherdict

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None     # unhashable; explicitly set to None for python2 compat

    @property
    def as_dict(self):
        ''' dict view of this object's fields and their values'''
        return dict((name, getattr(self, name)) for name in self._fields)

    def replace(self, **field_value_dict):
        '''Make a copy of self with fields set according to the argument dict'''
        fields = self.as_dict
        fields.update(field_value_dict)
        return type(self)(**fields)
