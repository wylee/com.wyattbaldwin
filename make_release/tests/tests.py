import doctest
import unittest

import make_release


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(make_release))
    return tests


class Tests(unittest.TestCase):
    def test(self):
        self.assertTrue(False)
