import sys
import unittest

from coverage import Coverage

from runcommands.args import arg
from runcommands.command import command


@command
def run_tests(
    with_coverage: arg(
        short_option="-c",
        inverse_short_option="-C",
        help="With coverage",
    ) = True,
):
    runner = unittest.TextTestRunner()
    loader = unittest.TestLoader()
    if with_coverage:
        coverage = Coverage(source=["./src"])
        coverage.start()
    tests = loader.discover("./tests")
    result = runner.run(tests)
    if with_coverage:
        coverage.stop()
        if not result.errors:
            coverage.report()


if __name__ == "__main__":
    sys.exit(run_tests.console_script())
