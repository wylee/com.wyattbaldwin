# Make a Release

Make a release of a Python package. This automates the tedious steps you
need to go through to make a release--bumping the version number,
tagging, etc.

It does _not_ (currently) create distributions or upload them to PyPI.

## Usage

    make-release --version 1.0 --next-version 2.0

## Steps

By default, all the following steps are run:

- Run the project's test suite (`python -m unittest discover` by
  default)
- Prepare the release by bumping the version number in various files and
  setting the release date in the change log file
- Merge the development branch into the target branch (e.g., `dev` to
  `main`)
- Create an annotated tag pointing at the merge commit (or at the prep
  commit when merging is disabled); if no tag name is specified, the
  release version is used as the tag name
- Resume development by bumping the version to the next anticipated
  version

Any of the steps can be skipped by passing the corresponding
`--no-<step>` flag.

### Tag Name

The tag name can be specified as a simple format string template. The
project `name` and release `version` will be injected (see below in the
Configuration section for an example).

## Configuration

Configuration can be done in `pyproject.toml` or `setup.cfg`. This is
most useful if you want to permanently change one of the default
options.

Use the long names of the command line options without the leading
dashes. For command line flags, set the value to `true` or `false`
(`1` and `0` also work).

For example, if your project only uses a single branch, you could
disable the merge step like so in `pyproject.toml`.

    # pyproject.toml
    [tool.make-release.args]
    merge = false
    tag-name = "{name}-{version}"
    test-command = "my-test-runner"

or like so in `setup.cfg`:

    # setup.cfg
    [make-release.args]
    merge = false
    tag-name = {name}-{version}
    test-command = my-test-runner

This also shows how to specify a tag name template that's derived from
the package `name` and the release `version`.

## Creating and Uploading Distribution

Once you've created a release with this tool, check out the tag for the
release and then run the following commands:

    poetry build           # if using poetry
    python setup.py sdist  # if using pip/setuptools
    twine upload dist/*    # in either case

NOTE: You'll need an account on pypi.org in order to upload
distributions with `twine`.

## Limitations

- Only git repositories are supported
- The package name detection assumes the root directory (i.e., the git
  repo name) is the same as the package name
- For the change log, only markdown files are supported; the change log
  is expected to use second-level (##) headings for each version's
  section (see this project's `CHANGELOG.md` for an example)
- Doesn't build or upload distributions
