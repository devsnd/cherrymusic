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
"""Dependency injection module.

Usage::

    >>> from cherrymusicserver import service
    >>> @service.provider('fooservice')     # register as provider
    ... class Foo(object):
    ...     def dofoo(self):
    ...         print('Foo!')
    ...
    >>> @service.user(myfoo='fooservice')   # become a user
    ... class User(object):
    ...     pass
    ...
    >>> service.provide(Foo)    # activate provider
    >>> User().myfoo.dofoo()    # provider is injected, and instantiated on first access
    Foo!

Without decorators::

    >>> service.provider('someservice')(someprovider)
    >>> service.provide(someprovider)

Shortcut::

    >>> service.provide(service.provider('someservice')(someprovider))

"""
import threading
from collections import Hashable

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


class ServiceError(Exception):
    pass


class ServiceNotAvailableError(ServiceError):
    """No provider is active for a given service handle."""
    pass


class ProviderUnknownError(ServiceError):
    """An object is not registered as a provider."""
    pass


__registry = {}
__provider_factories = {}
__providercache = {}


def provider(handle):
    """Register a service provider for a service handle.

    To actually use a provider, activate it by calling :func:`provide` after
    registering.

    handle : Hashable, not None
        The handle the provided service goes by.

    Returns: Decorator
        A function that takes the provider as its sole argument.
        The provider must be Hashable and not None.
    """
    assert handle is not None
    assert isinstance(handle, Hashable)

    def decorator(type_):
        assert type_ is not None
        assert isinstance(type_, Hashable)
        __registry[type_] = handle
        return type_

    return decorator


def user(**requirements):
    """Inject required service providers into the decorated class.

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


def provide(provider, args=(), kwargs={}):
    """Activate a provider for the service it registered for.

    Callable providers will not be called (e.g. classes instantiated) until
    they are requested (:func:`get`) by some user.

    provider :
        The provider as it was registered: that is, if a class was registered,
        supply the class, not an instance.
    args, kwargs :
        Pass on arguments to a callable provider.

    """
    assert callable(provider) or not (args or kwargs)
    handle = _gethandle(provider)
    __provider_factories[handle] = _ProviderFactory.get(provider, args, kwargs)
    __providercache.pop(handle, None)
    log.d('service %r: now provided by %r', handle, provider)


def get(handle):
    """Request the provider for the service identified by ``handle``.

    If a callable object was registered for the handle, the actual provider
    will be the result of calling the callable. The call will be made when the
    handle is first requested.

    For example, if a class was registered as provider, an instance of the
    class will be created on the first request and returned to all users of the
    service.
    """
    try:
        return __providercache[handle]
    except KeyError:
        return _createprovider(handle)


class require(object):
    """Descriptor for attributes that contain a service provider.

        >>> import cherrymusicserver.service as service
        >>> class ServiceUser(object):
        ...     myfoo = service.require('fooservice')
    """
    def __init__(self, handle):
        self.handle = handle

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self.handle)

    def __get__(self, instance, owner):
        return get(self.handle)


def _gethandle(provider):
    try:
        return __registry[provider]
    except KeyError:
        raise ProviderUnknownError(provider)


def _createprovider(handle):
    try:
        factory = __provider_factories[handle]
    except KeyError:
        raise ServiceNotAvailableError(handle)
    return __providercache.setdefault(handle, factory())


class _ProviderFactory(object):
    """High security facility to contain cyclic dependency and multithreading
    issues. Manage instances to allow one factory per provider, which guards
    against dependency cycles.

    .. warning:: Always use :meth:`get` to obtain instances.
    """

    master_lock = threading.Lock()

    __factories = {}

    @classmethod
    def get(cls, provider, args, kwargs):
        with cls.master_lock:
            if provider in cls.__factories:
                instance = cls.__factories[provider]
            else:
                instance = cls.__factories.setdefault(provider, cls(provider))
            instance.args = args
            instance.kwargs = kwargs
        return instance

    def __init__(self, provider, args=(), kwargs={}):
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
            with self.master_lock:
                lock = local.__dict__.setdefault('lock', threading.Lock())
        return lock

    def __call__(self):
        if self.lock.locked():
            raise MutualDependencyBreak(self.provider)
        with self.lock:
            value = self._make()
        return value

    def _make(self):
        if callable(self.provider):
            return self.provider(*self.args, **self.kwargs)
        return self.provider
