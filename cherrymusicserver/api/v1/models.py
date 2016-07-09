# -*- coding: utf-8 -*- #
#
# CherryMusic - a standalone music server
# Copyright (c) 2012-2015 Tom Wallroth & Tilman Boerner
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

from backport import callable

class Model(object):
    """ Base class for CherryMusic business objects.

        If offers three important features:

        - The constructor will set all keyword arguments as attributes;
        - a subset of attributes ("fields"), to represent the visible state
          of a model object, with default values;
        - an :meth:`as_dict` method that returns a dict representation of
          an object's fields.

        Therefore, it should be possible to recreate an object from its dict.

        To make a field attribute, simply declare a class attribute with
        a :cls:`Model.Field` value::

            class Foo(Model):
                bar = Model.Field(defaultvalue)

        If ``defaultvalue`` is callable, it will be called with the model
        object as its sole argument when the field is initialized, and the
        return value will be used as the actual default.

        Fields will be listed as "Data Descriptors" in the ``help()`` of
        a model class or object.
    """

    class Field(object):

        @classmethod
        def fields_as_dict(cls, model):
            "get a copy of the model's field-value dict"
            return cls._values(model).copy()

        @classmethod
        def _init_fields(cls, model, valuedict):
            """ Initialize all fields defined for the model's class by
                assigning them their attribute names as names and putting their
                default values into valuedict.
            """
            modelcls = type(model)
            for name in (n for n in dir(modelcls) if not n.startswith('__')):
                field = getattr(modelcls, name)
                if not isinstance(field, Model.Field):
                    continue
                if not getattr(field, 'name', None):
                    field.name = name
                default = field.default
                value = default(model) if callable(default) else default
                valuedict[name] = value

        @classmethod
        def _values(cls, model):
            """ Get the value dict used for all fields of the model.
                If it doesn't exist, create it and initialize all fields.
            """
            try:
                return model.__values
            except AttributeError:
                model.__values = v = {}
                cls._init_fields(model, v)
                return v

        def __init__(self, default):
            self.default = default

        def __get__(self, model, modelcls):
            if model is None:
                return self
            try:
                return self._values(model)[self.name]
            except KeyError:
                raise AttributeError(self.name)  # field value has been deleted

        def __set__(self, model, value):
            self._values(model)[self.name] = value

        def __delete__(self, model):
            del self._values(model)[self.name]

        def __repr__(self):                                  # pragma: no cover
            return '{cls}({default!r})'.format(
                cls=type(self).__name__, default=self.default)

    id = Field(None)
    id.__doc__ = """
    value to uniquely identify the model (given its class) on the
    server, or None"""

    cls = Field(lambda s: type(s).__name__)
    cls.__doc__ = "string to identify the class of the model"

    def __init__(self, **kwargs):
        """ initializes the model and sets keyword arguments as attributes """
        for name, value in kwargs.items():
            setattr(self, name, value)

    def as_dict(self):
        """ a dict representation of the model's fields and their values """
        return self.Field.fields_as_dict(self)
