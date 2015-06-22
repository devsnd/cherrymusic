import imp
from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)

class PluginManager(object):
    _event_listeners = defaultdict(list)

    class Event:
        LOGGED_IN = 'LOGGED_IN'
        GET_MOTD = 'GET_MOTD'

    @classmethod
    def register_event(cls, event, callback):
        if event not in dir(PluginManager.Event):
            logger.error('Cannot register unknown event %s' % event)
            return False
        if not callable(callback):
            logger.error('Callback %s must be callable!' % callback)
            return False
        PluginManager._event_listeners[event].append(callback)

    @classmethod
    def unregister_event(cls, event, callback):
        PluginManager._event_listeners[event] = [
            c for c in PluginManager._event_listeners[event] if c != callback
        ]

    @classmethod
    def digest(cls, event, user, payload):
        for callback in PluginManager._event_listeners[event]:
            payload = callback(user, payload)
        return payload


    @classmethod
    def initialize_plugins(cls):
        file, pathname, description = imp.find_module('plugins')
        for plugin_name in os.listdir(pathname):
            if plugin_name.startswith('__'):
                continue
            plugin = __import__('plugins.' + plugin_name)
            getattr(plugin, plugin_name).activate()
