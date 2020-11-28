from runcommands.commands import local
from runcommands.util import confirm, printer, prompt

from .util import get_current_branch, print_step_header, update_line


def prepare_release(info):
    version = info.version
    print_step_header("Preparing release", version, "on", info.date)

    current_branch = get_current_branch()

    local(("git", "checkout", info.dev_branch))

    if info.pyproject_file:
        quote = info.pyproject_version_quote
        update_line(
            info.pyproject_file,
            info.pyproject_version_line_number,
            f"version = {quote}{version}{quote}",
        )

    if info.version_file:
        quote = info.version_quote
        update_line(
            info.version_file,
            info.version_line_number,
            f"__version__ = {quote}{version}{quote}",
        )

    update_line(
        info.change_log,
        info.change_log_line_number,
        f"## {version} - {info.date}",
    )

    commit_files = (info.pyproject_file, info.version_file, info.change_log)
    local(("git", "diff", *commit_files))

    if info.confirmation_required:
        confirm("Commit these changes?", abort_on_unconfirmed=True)
    else:
        printer.warning("Committing changes")

    msg = f"Prepare {info.name} release {version}"
    msg = prompt("Commit message", default=msg)
    local(("git", "commit", commit_files, "-m", msg))

    local(("git", "checkout", current_branch))
