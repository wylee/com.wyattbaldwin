import pathlib
import shutil
import string
import subprocess
import sys

from runcommands.args import arg
from runcommands.command import command

PYPROJECT_TEMPLATE = """\
[tool.poetry]
name = "${qualified_name}"
version = "${version}.dev0"
description = "${description}"
authors = ["Wyatt Baldwin <self@wyattbaldwin.com>"]
repository = "${repository}"

packages = [
    { include = "${name}", from = "src" }
]

include = [
    "CHANGELOG.md",
    "README.md",
]

[tool.poetry.dependencies]
python = "^3.6"

[tool.poetry.dev-dependencies]
"com.wyattbaldwin" = { path = "../com.wyattbaldwin", develop = true }
black = { version = "*", allow-prereleases = true }
coverage = "*"

[tool.make-release.args]
merge = false
tag-name = "{name}-{version}"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
"""


README_TEMPLATE = """\
# ${title}

${description}

## Usage

    >>> import ${name}

"""


CHANGELOG_TEMPLATE = """\
# ${title}

## ${version} - unreleased

In progress...

"""


TESTS_TEMPLATE = """\
import doctest
import unittest

import ${name}


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(${name}))
    return tests


class Tests(unittest.TestCase):
    def test(self):
        self.assertTrue(False)
"""


@command
def make_package(
    name: arg(help="Package name"),
    title: arg(help="Package title"),
    version: arg(
        short_option="-v",
        help="Package version",
    ) = "1.0a1",
    description: arg(
        short_option="-d",
        help="Package description",
    ) = None,
    overwrite: arg(
        short_option="-o",
        help="Overwrite existing package",
    ) = False,
):
    name_parts = name.split(".")
    qualified_name = f"com.wyattbaldwin.{name}"
    description = description or title
    repository = f"https://github.com/wylee/com.wyattbaldwin/tree/dev/{name}"

    src_dir = pathlib.Path(__file__).parent
    root_dir = src_dir.parent.parent.parent.parent

    package_dir = root_dir / name
    pyproject_path = package_dir / "pyproject.toml"
    readme_path = package_dir / "README.md"
    changelog_path = package_dir / "CHANGELOG.md"

    src_dir = package_dir.joinpath("src", *name_parts)
    init_path = src_dir / "__init__.py"

    tests_dir = package_dir.joinpath("tests")
    tests_path = tests_dir / "tests.py"

    template_vars = {
        "name": name,
        "qualified_name": qualified_name,
        "version": version,
        "title": title,
        "heading": "+" * len(title),
        "description": description,
        "repository": repository,
    }

    print(f"Creating new package: {name} -> {qualified_name}")
    print(f"Root directory: {root_dir.absolute()}")
    print(f"Package directory: {package_dir.absolute()}")
    print(f"Source directory: {src_dir.absolute()}")
    print(f"Test directory: {tests_dir.absolute()}")

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    else:
        if result.stdout or result.stderr:
            lines = []
            for line in result.stdout.splitlines():
                if not (line.startswith(" M ") and line.endswith("make_package.py")):
                    lines.append(line)
            lines.extend(result.stderr.splitlines())
            if lines:
                print("com.wyattbaldwin repo not clean; aborting\n")
                subprocess.run(["git", "status"])
                return 1

    # Package -------------------------------------------------------------------------

    if package_dir.exists():
        if overwrite:
            shutil.rmtree(package_dir)
            print(f"Removed existing package directory: {package_dir}")
        else:
            print(f"Path exists: {package_dir}")
            return 1

    create_dir(package_dir)
    create_file(pyproject_path, PYPROJECT_TEMPLATE, template_vars)
    create_file(readme_path, README_TEMPLATE, template_vars)
    create_file(changelog_path, CHANGELOG_TEMPLATE, template_vars)

    # Source --------------------------------------------------------------------------

    create_dir(src_dir)
    create_file(init_path, '__version__ = "${version}.dev0"', template_vars)

    # Tests ---------------------------------------------------------------------------

    create_dir(tests_dir)
    create_file(tests_path, TESTS_TEMPLATE, template_vars)

    return 0


def create_dir(path):
    path.mkdir(parents=True)
    print(f"Created directory: {path}")


def create_file(path, template=None, template_vars=None):
    if template is None:
        path.touch()
    else:
        template = string.Template(template)
        content = template.substitute(template_vars or {})
        with path.open("w") as fp:
            fp.write(content)
    print(f"Created file: {path}")


if __name__ == "__main__":
    sys.exit(make_package.console_script())
