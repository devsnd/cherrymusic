import os
import pkgutil
import re
import sys
import unittest

pattern = re.compile('test.*')
loader = unittest.defaultTestLoader
runner = unittest.TextTestRunner()

from . import discover_tests

class Fail(unittest.TestCase):
    def testfail(self):
        self.fail()

if __name__ == '__main__':
    # test = loader.suiteClass(loader.loadTestsFromTestCase(Fail))
    test = loader.suiteClass(list(discover_tests()))
    result = runner.run(test)
    sys.exit(not result.wasSuccessful())
