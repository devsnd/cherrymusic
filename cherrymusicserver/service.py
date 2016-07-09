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
""" Dependency injection and other facilities to match providers of services
    with their users.

    Nature and interface of a service are left for the concerned parties to
    agree on; all this module knows about the service is its name, or "handle".

    Basic usage::

        >>> pizza = object()
        >>> service.provide('pizzaservice', pizza)
        >>> pizza is service.get('pizzaservice')
        True

    Types as providers and users::

        >>> class PizzaService(object):
        ...     pass
        ...
        >>> @service.user(mypizza='pizzaservice')     # become a user
        ... class PizzaUser(object):
        ...     pass
        ...
        >>> user = PizzaUser()
        >>> service.provide('pizzaservice', PizzaService)
        >>> isinstance(user.mypizza, PizzaService)    # provider as attribute
        True
"""
import threading

from cherrymusicserver import log


class MutualDependencyBreak(Exception):
    """Raised when mutually dependent providers are trying to instantiate
    each other in their constructors.

    This happens while creating a provider that is part of a dependency
    cycle; when it is allowed, in its constructor, to access a dependency
    that's also part of the cycle, a singularity is spawned which implodes the
    universe. This exception is raised to prevent that.

    In general, don't create cyclic dependencies. It's bad for your brain and
    also a sure sign of a problematic program architecture. When confronted
    with a mutual dependency, extract a third class from one of the offenders
    for both to depend on.
    """
    pass


__provider_factories = {}
__providercache = {}


def provide(handle, provider, args=(), kwargs={}):
    """ Activate a provider for the service identified by ``handle``,
        replacing a previous provider for the same service.

        If the provider is a ``type``, an instance will be created as the
        actual provider. Instantiation is lazy, meaning it will be deferred
        until the provider is requested (:func:`get`) by some user.

        To use a type as a provider, you need to wrap it into something that is
        not a type.

        handle : str
            The name of the serivce.
        provider :
            An object that provides the service, or a type that instantiates
            such objects. Instantiation will happen on the first get call.
        args, kwargs :
            Pass on arguments to a type.
    """
    assert isinstance(provider, type) or not (args or kwargs)
    __provider_factories[handle] = _ProviderFactory.get(provider, args, kwargs)
    __providercache.pop(handle, None)
    log.d('service %r: now provided by %r', handle, provider)


def get(handle):
    """Request the provider for the service identified by ``handle``.

    If a type was registered for the handle, the actual provider will be the
    result of instantiating the type when it is first requested.

    Although the goal is to create only one instance, it is possible that
    different threads see different instances.
    """
    try:
        return __providercache[handle]
    except KeyError:
        return _createprovider(handle)


class require(object):
    """Descriptor to make a service provider available as a class attribute.

        >>> import cherrymusicserver.service as service
        >>> class ServiceUser(object):
        ...     mypizzas = service.require('pizzaservice')
    """
    def __init__(self, handle):
        self.handle = handle

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self.handle)

    def __get__(self, instance, owner):
        return get(self.handle)


def user(**requirements):
    """ Class deocrator to inject service providers as attributes into the
        decorated class.

        requirements : name=handle
            Create :class:`require` descriptor attributes in the class:
            ``name = require(handle)``.

        Returns: Class Decorator
            A function that takes the user class as its sole argument.
    """
    def clsdecorator(cls):
        for attribute, handle in requirements.items():
            setattr(cls, attribute, require(handle))
        return cls
    return clsdecorator


def _createprovider(handle):
    try:
        factory = __provider_factories[handle]
    except KeyError:
        raise LookupError('Service not available: {0!r}'.format(handle))
    return __providercache.setdefault(handle, factory.make())


class _ProviderFactory(object):
    """ High security facility to contain cyclic dependency and multithreading
        issues.

        Factory instances guard against dependency cycles by raising a
        :class:`MutualDependencyBreak` when mutually dependent providers
        try to instantiate each other.
    """

    _master_lock = threading.Lock()

    __factories = {}

    @classmethod
    def get(cls, provider, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        with cls._master_lock:
            try:
                factory = cls.__factories[id(provider)]
                factory.args = args
                factory.kwargs = kwargs
            except KeyError:
                factory = cls(provider, args, kwargs)
                cls.__factories[id(provider)] = factory
            return factory

    def __init__(self, provider, args=(), kwargs={}):
        assert self._master_lock.locked(), 'use .get(...) to obtain instances'
        self.provider = provider
        self.args = args
        self.kwargs = kwargs
        self.__threadlocal = threading.local()

    @property
    def lock(self):
        """Thread-local: dependendy issues will happen inside the same thread,
        so don't compete with other threads."""
        local = self.__threadlocal
        try:
            lock = local.lock
        except AttributeError:
            with self._master_lock:
                lock = local.__dict__.setdefault('lock', threading.Lock())
        return lock

    def make(self):
        """ Return a provider instance.

            Raises : :cls:`MutualDependencyBreak`
                If called recursively within the same thread, which happens
                when mutually dependent providers try to instantiate each other.
        """
        if self.lock.locked():
            raise MutualDependencyBreak(self.provider)
        with self.lock:
            if isinstance(self.provider, (type, type(Python2OldStyleClass))):
                return self.provider(*self.args, **self.kwargs)
            return self.provider


class Python2OldStyleClass:
    """In Python2, I am a ``classobj`` which is not the same as a ``type``."""
    pass
