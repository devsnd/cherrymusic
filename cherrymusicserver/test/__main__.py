import os
import pkgutil
import re
import sys
import unittest

pattern = re.compile('test.*')
loader = unittest.defaultTestLoader
runner = unittest.TextTestRunner()


def discover_tests():
    package = __package__
    packdir = __file__.rsplit(os.path.sep, 1)[0]
    parent = None
    modules = (i[1] for i in pkgutil.iter_modules([packdir]))
    testmodules = ('.'.join((package, m)) for m in modules if pattern.match(m))
    for mname in testmodules:
        yield loader.loadTestsFromName(mname, parent)

class Fail(unittest.TestCase):
    def testfail(self):
        self.fail()

if __name__ == '__main__':
    # test = loader.suiteClass(loader.loadTestsFromTestCase(Fail))
    test = loader.suiteClass(list(discover_tests()))
    result = runner.run(test)
    sys.exit(not result.wasSuccessful())
