import doctest

from make_release import util


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(util))
    return tests
