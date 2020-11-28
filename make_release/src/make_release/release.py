import datetime
import pathlib

from runcommands.args import arg
from runcommands.command import command
from runcommands.util import abort, printer, confirm
from runcommands.commands.local import local

from .prepare import prepare_release
from .merge import merge_to_target_branch
from .tag import create_release_tag
from .resume import resume_development
from .util import (
    ReleaseInfo,
    find_change_log,
    find_change_log_section,
    find_version_file,
    get_current_branch,
    get_current_version,
    get_next_version,
    print_info,
    print_step,
    print_step_header,
)


@command(read_config=True)
def make_release(
    # Steps
    test: arg(
        short_option="-e",
        help="Run tests first",
    ) = True,
    prepare: arg(
        short_option="-p",
        help="Run release preparation tasks",
    ) = True,
    merge: arg(
        short_option="-m",
        help="Run merge tasks",
    ) = True,
    tag: arg(
        short_option="-t",
        help="Create release tag",
    ) = True,
    resume: arg(
        short_option="-r",
        help="Run resume development tasks",
    ) = True,
    test_command: arg(
        short_option="-c",
        help="Test command",
    ) = None,
    # Step config
    name: arg(
        short_option="-n",
        help="Release/package name [base name of CWD]",
    ) = None,
    version: arg(
        short_option="-v",
        help="Version to release",
    ) = None,
    version_file: arg(
        short_option="-V",
        help="File __version__ is in [search typical files]",
    ) = None,
    date: arg(
        short_option="-d",
        help="Release date [today]",
    ) = None,
    dev_branch: arg(
        short_option="-b",
        help="Branch to merge from [current branch]",
    ) = None,
    target_branch: arg(
        short_option="-B",
        help="Branch to merge into [prod]",
    ) = "prod",
    tag_name: arg(
        short_option="-a",
        help=(
            "Release tag name; {name} and {version} in the tag name "
            "will be substituted [version]"
        ),
    ) = None,
    next_version: arg(
        short_option="-w",
        help="Anticipated version of next release",
    ) = None,
    # Other
    yes: arg(
        short_option="-y",
        no_inverse=True,
        help="Run without being prompted for any confirmations",
    ) = False,
    show_version: arg(
        short_option="-s",
        long_option="--show-version",
        no_inverse=True,
        help="Show make-release version and exit",
    ) = False,
):
    """Make a release.

    Tries to guess the release version based on the current version and
    the next version based on the release version.

    Steps:
        - Prepare release:
            - Update ``version`` in ``pyproject.toml`` (if present)
            - Update ``__version__`` in version file (if present;
              typically ``package/__init__.py`` or
              ``src/package/__init__.py``)
            - Update next version header in change log
            - Commit version file and change log with prepare message
        - Merge to target branch (``prod`` by default):
            - Merge current branch into target branch with merge message
        - Create tag:
            - Add annotated tag for latest version; when merging, the
              tag will point at the merge commit on the target branch;
              when not merging, the tag will point at the prepare
              release commit on the current branch
        - Resume development:
            - Update version in ``pyproject.toml`` to next version (if
              present)
            - Update version in version file to next version (if
              present)
            - Add in-progress section for next version to change log
            - Commit version file and change log with resume message

    Caveats:
        - The next version will have the dev marker ".dev0" appended to
          it
        - The change log must be in Markdown format; release section
          headers must be second-level (i.e., start with ##)
        - The change log must be named CHANGELOG or CHANGELOG.md
        - The first release section header in the change log will be
          updated, so there always needs to be an in-progress section
          for the next version
        - Building distributions and uploading to PyPI isn't handled;
          after creating a release, build distributions using
          ``python setup.py sdist`` or ``poetry build`` (for example)
          and then upload them with ``twine upload``

    """
    if show_version:
        from . import __version__

        print(f"make-release version {__version__}")
        return

    cwd = pathlib.Path.cwd()
    name = name or cwd.name

    printer.hr("Releasing", name)
    print_step("Testing?", test)
    print_step("Preparing?", prepare)
    print_step("Merging?", merge)
    print_step("Tagging?", tag)
    print_step("Resuming development?", resume)

    if merge:
        if dev_branch is None:
            dev_branch = get_current_branch()
        if dev_branch == target_branch:
            abort(1, f"Dev branch and target branch are the same: {dev_branch}")

    pyproject_file = pathlib.Path("pyproject.toml")
    if pyproject_file.is_file():
        pyproject_version_info = get_current_version(pyproject_file, "version")
        (
            pyproject_version_line_number,
            pyproject_version_quote,
            pyproject_current_version,
        ) = pyproject_version_info
    else:
        pyproject_file = None
        pyproject_version_line_number = None
        pyproject_version_quote = None
        pyproject_current_version = None

    if version_file:
        version_file = pathlib.Path(version_file)
        version_info = get_current_version(version_file)
        version_line_number, version_quote, current_version = version_info
    else:
        version_info = find_version_file()
        if version_info is not None:
            (
                version_file,
                version_line_number,
                version_quote,
                current_version,
            ) = version_info
        else:
            version_file = None
            version_line_number = None
            version_quote = None
            current_version = pyproject_current_version

    if (
        current_version
        and pyproject_current_version
        and current_version != pyproject_current_version
    ):
        abort(
            2,
            f"Version in pyproject.toml and "
            f"{version_file.relative_to(cwd)} don't match",
        )

    if not version:
        if current_version:
            version = current_version
        else:
            message = (
                "Current version not set in version file, so release "
                "version needs to be passed explicitly"
            )
            abort(3, message)

    if tag_name:
        tag_name = tag_name.format(name=name, version=version)
    else:
        tag_name = version

    date = date or datetime.date.today().isoformat()

    if not next_version:
        next_version = get_next_version(version)

    change_log = find_change_log()
    change_log_line_number = find_change_log_section(change_log, version)

    info = ReleaseInfo(
        name,
        dev_branch,
        target_branch,
        pyproject_file,
        pyproject_version_line_number,
        pyproject_version_quote,
        version_file,
        version_line_number,
        version_quote,
        version,
        tag_name,
        date,
        next_version,
        change_log,
        change_log_line_number,
        not yes,
    )

    print_info("Version:", info.version)
    print_info("Release date:", info.date)
    if merge:
        print_info("Dev branch:", dev_branch)
        print_info("Target branch:", target_branch)
    if tag:
        print_info("Tag name:", tag_name)
    print_info("Next version:", info.next_version)

    if info.confirmation_required:
        msg = f"Continue with release?: {info.version} - {info.date}"
        confirm(msg, abort_on_unconfirmed=True)
    else:
        printer.warning("Continuing with release: {info.version} - {info.date}")

    if test:
        print_step_header("Testing")
        if test_command is None:
            if (cwd / "tests").is_dir():
                test_command = "python -m unittest discover tests"
            else:
                test_command = "python -m unittest discover ."
        local(test_command, echo=True)
    else:
        printer.warning("Skipping tests")

    if prepare:
        prepare_release(info)

    if merge:
        merge_to_target_branch(info)

    if tag:
        create_release_tag(info, merge)

    if resume:
        resume_development(info)
