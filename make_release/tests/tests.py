import doctest

import make_release


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(make_release))
    return tests
