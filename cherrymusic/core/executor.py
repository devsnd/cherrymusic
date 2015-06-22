class DelayedExecutor(object):
    '''
    This class should be hooked up to a post-request signal, so that some time consuming tasks
    can be performed after the request was returned to the client.
    '''
    _tasks = []

    @classmethod
    def delay(cls, method, *args, **kwargs):
        cls._tasks.append((method, args, kwargs))

    @classmethod
    def execute(cls):
        for method, args, kwargs in cls._tasks:
            method(*args, **kwargs)
        cls._tasks = []
