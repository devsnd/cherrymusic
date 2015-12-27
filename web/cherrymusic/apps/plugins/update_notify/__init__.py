def get_motd(user, payload):
    if user.is_staff:
        return 'you are an admin! hi.'
    return payload

def activate():
    from cherrymusic.apps.core.pluginmanager import PluginManager
    PluginManager.register_event(PluginManager.Event.GET_MOTD, get_motd)

def deactivate():
    from cherrymusic.apps.core.pluginmanager import PluginManager
    PluginManager.unregister_event(PluginManager.Event.GET_MOTD, get_motd)