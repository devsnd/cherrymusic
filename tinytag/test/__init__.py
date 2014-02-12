import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

if __name__ == '__main__':
    unittest.main()
