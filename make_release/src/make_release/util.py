import pathlib
import re
from collections import namedtuple

from runcommands.commands import local
from runcommands.util import abort, printer

ReleaseInfo = namedtuple(
    "ReleaseInfo",
    (
        "name",
        "source_branch",
        "target_branch",
        "pyproject_file",
        "pyproject_version_line_number",
        "pyproject_version_quote",
        "version_file",
        "version_line_number",
        "version_quote",
        "version",
        "tag_name",
        "date",
        "next_version",
        "change_log",
        "change_log_line_number",
        "confirmation_required",
    ),
)


def find_change_log():
    change_log_candidates = ["CHANGELOG", "CHANGELOG.md"]
    for candidate in change_log_candidates:
        path = pathlib.Path.cwd() / candidate
        if path.is_file():
            return path
    abort(6, f"Could not find change log; tried {', '.join(change_log_candidates)}")


def find_change_log_section(change_log, version):
    # Find the first line that starts with '##'. Extract the version and
    # date from that line. The version must be the specified release
    # version OR the date must be the literal string 'unreleased'.

    # E.g.: ## 1.0.0 - unreleased
    change_log_header_re = r"^## (?P<version>.+) - (?P<date>.+)$"

    with change_log.open() as fp:
        for line_number, line in enumerate(fp):
            match = re.search(change_log_header_re, line)
            if match:
                found_version = match.group("version")
                found_date = match.group("date")
                if found_version == version:
                    if found_date != "unreleased":
                        printer.warning("Re-releasing", version)
                elif found_date == "unreleased":
                    if found_version != version:
                        printer.warning("Replacing", found_version, "with", version)
                else:
                    msg = (
                        f"Expected version {version} or release date "
                        f'"unreleased"; got:\n\n    {line}'
                    )
                    abort(7, msg)
                return line_number

    abort(8, "Could not find section in change log")


def find_line_ending(line):
    candidates = ("\r\n", "\n", "\r")
    for candidate in candidates:
        if line.endswith(candidate):
            return candidate
    raise ValueError(r"Line doesn't end with a known line ending: \r\n, \n, or \r")


def find_version_file():
    # Try to find __version__ in:
    #
    # - package/__init__.py
    # - namespace_package/package/__init__.py
    # - src/package/__init__.py
    # - src/namespace_package/package/__init__.py
    cwd = pathlib.Path.cwd()
    candidates = []
    candidates.extend(cwd.glob("*/__init__.py"))
    candidates.extend(cwd.glob("*/*/__init__.py"))
    candidates.extend(cwd.glob("src/*/__init__.py"))
    candidates.extend(cwd.glob("src/*/*/__init__.py"))
    for candidate in candidates:
        result = get_current_version(candidate, "__version__", False)
        if result is not None:
            return (candidate,) + result
    candidates = "\n    ".join(str(candidate) for candidate in candidates)
    printer.warning(
        f"Could not find file containing __version__; tried:\n    {candidates}",
    )
    return None


def get_current_branch():
    result = local("git rev-parse --abbrev-ref HEAD", stdout="capture")
    return result.stdout.strip()


def get_latest_tag():
    result = local("git rev-list --tags --max-count=1", stdout="capture")
    revision = result.stdout.strip()
    result = local(("git", "describe", "--tags", revision), stdout="capture")
    tag = result.stdout.strip()
    return tag


def get_current_version(file, name, abort_on_not_found=True):
    # Extract current version from __version__ in version file.
    #
    # E.g.: __version__ = '1.0.dev0'
    version_re = (
        rf"""^{name}"""
        r""" *= *"""
        r"""(?P<quote>['"])((?P<version>.+?)(?P<dev_marker>\.dev\d+)?)?\1 *$"""
    )
    with file.open() as fp:
        for line_number, line in enumerate(fp):
            match = re.search(version_re, line)
            if match:
                return line_number, match.group("quote"), match.group("version")
    if abort_on_not_found:
        abort(4, f"Could not find {name} in {file}")


def get_next_version(current_version):
    """Get next version based on current version.

    This handles the following formats:

    - 1.0         -> 1.1
    - 1.0.post1   -> 1.1
    - 1.0.0       -> 1.1.0
    - 1.0.0.post1 -> 1.1.0
    - 0.0.1       -> 0.0.2
    - 0.0.1.post1 -> 0.0.2
    - 1.0a1       -> 1.0a2
    - 1.0a1.post1 -> 1.0a2

    Note that in all cases any suffix will be removed (`.post1` in these
    examples).

    Examples::

        >>> get_next_version("1.0")
        '1.1'
        >>> get_next_version("1.1.post1")
        '1.2'

        >>> get_next_version("1.0.0")
        '1.1.0'
        >>> get_next_version("1.2.0")
        '1.3.0'
        >>> get_next_version("1.0.1")
        '1.1.0'
        >>> get_next_version("1.0.1.post1")
        '1.1.0'
        >>> get_next_version("1.2.1.post1")
        '1.3.0'

        >>> get_next_version("0.0.0")
        '0.0.1'
        >>> get_next_version("0.0.1")
        '0.0.2'
        >>> get_next_version("0.0.2.post1")
        '0.0.3'

        >>> get_next_version("1.0a1")
        '1.0a2'
        >>> get_next_version("1.0a2.post1")
        '1.0a3'

    """
    next_version_re = r"^(?P<major>\d+)\.(?P<minor>\d+)(?P<rest>.*)$"
    match = re.search(next_version_re, current_version)

    if match:
        major = match.group("major")
        minor = match.group("minor")

        major = int(major)
        minor = int(minor)

        rest = match.group("rest")
        patch_re = r"^\.(?P<patch>\d+)(?P<rest>.*)$"
        patch_match = re.search(patch_re, rest)

        if patch_match:
            # <major>.<minor>.<patch><rest>
            #
            # Example: 1.0.2
            # Example: 1.0.2.post1
            #
            # If the major and minor versions are both 0, increment the
            # patch version, if possible. In all other cases, increment
            # the minor version and set the patch version to 0.
            patch = patch_match.group("patch")
            patch = int(patch)
            if (major, minor) == (0, 0):
                patch = int(patch) + 1
            else:
                minor += 1
                patch = 0
            next_version = f"{major}.{minor}.{patch}"
        else:
            pre_re = r"^(?P<pre_type>a|b|rc)(?P<pre_version>\d+)(?P<rest>.*)$"
            pre_match = re.search(pre_re, rest)
            if pre_match:
                # <major>.<minor><prerelease type><prerelease version>
                #
                # Example: 1.0a2
                # Example: 1.0a2.post1
                #
                # Increment prerelease version.
                pre_type = pre_match.group("pre_type")
                pre_version = pre_match.group("pre_version")
                pre_version = int(pre_version)
                pre_version += 1
                next_version = f"{major}.{minor}{pre_type}{pre_version}"
            else:
                # <major>.<minor><rest>
                #
                # Example: 1.0.post1
                #
                # Increment prerelease version.
                minor += 1
                next_version = f"{major}.{minor}"

        return next_version

    abort(
        5,
        f"Could not guess next version from version {current_version!r}.\n"
        "Use the -w option to specify the next version manually.",
    )


def print_info(label, arg, *args):
    printer.info(label, end=" ", flush=True)
    printer.print(arg, *args)


def print_step(message, flag):
    printer.info(message, end=" ", flush=True)
    printer.print("yes" if flag else "no", color="green" if flag else "red")


def print_step_header(arg, *args):
    printer.print("\n")
    printer.header(arg, *args)


def update_line(path, line_to_update, new_content):
    """Update line with new content.

    Do *not* include the trailing newline--the line ending of the
    existing line will be appended automatically.

    """
    lines = []
    with path.open("r", newline="") as fp:
        for line_number, line in enumerate(fp):
            if line_number == line_to_update:
                lines.append(new_content)
                lines.append(find_line_ending(line))
            else:
                lines.append(line)
    assert all(str(item) for item in lines), repr(lines)
    with path.open("w", newline="") as fp:
        fp.writelines(lines)
