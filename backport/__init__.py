import sys

if sys.version_info < (3,0):
    from . import urllib
    input = raw_input
else:
    input = input

if sys.version_info < (3,2):
    import optparse as argparse
    argparse.ArgumentParser = argparse.OptionParser
    argparse.ArgumentParser.add_argument = argparse.ArgumentParser.add_option
    argparse.ArgumentParser.__parse_args__ = argparse.ArgumentParser.parse_args
    def parseargs(self):
        return self.__parse_args__()[0]
    argparse.ArgumentParser.parse_args = parseargs
else:
    import argparse


if (3,) <= sys.version_info < (3, 2):
    import collections
    def callable(x):
        """ isinstance(x, collections.Callable)"""
        return isinstance(x, collections.Callable)
else:
    callable = callable


if sys.version_info < (3,):
    def with_metaclass(metacls):
        class MetaclassBearer(object):
            __metaclass__ = metacls
        return MetaclassBearer
else:
    def with_metaclass(metacls):
        _clsname = 'MetaclassBearer_' + metacls.__name__
        _globals = {'__name__': globals()['__name__']}
        _locals = {'metacls': metacls}
                                # hide python 3 syntax from py2 interpreter:
        exec(
            "class {0}(metaclass=metacls): pass".format(_clsname),
            _globals, _locals)
        return _locals[_clsname]
