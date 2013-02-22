import os
import pkgutil
import re
import unittest

pattern = re.compile('test.*')
loader = unittest.defaultTestLoader


class All(unittest.TestSuite):
    def __init__(self):
        super(self.__class__, self).__init__(discover_tests())


def discover_tests():
    package = __package__ or __name__
    packdir = __file__.rsplit(os.path.sep, 1)[0]
    parent = None
    modules = (i[1] for i in pkgutil.iter_modules([packdir]))
    testmodules = ('.'.join((package, m)) for m in modules if pattern.match(m))
    for mname in testmodules:
        yield loader.loadTestsFromName(mname, parent)

if __name__ == '__main__':
    unittest.main()

