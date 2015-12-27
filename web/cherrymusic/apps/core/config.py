from cherrymusic.apps.core import pathprovider


class Config(dict):
    _config = None

    @classmethod
    def get_config(cls):
        if cls._config is None:
            print('''STUB: IMPLEMENT CONFIG LOADER''')
            pathprovider.getConfigPath()
            cls._config = Config()
        return cls._config