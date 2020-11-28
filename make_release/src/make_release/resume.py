from runcommands.commands import local
from runcommands.util import confirm, printer, prompt

from .util import get_current_branch, print_step_header, update_line


def resume_development(info):
    next_version = info.next_version
    dev_version = f"{next_version}.dev0"
    print_step_header(
        f"Resuming development of {info.name} at {next_version} " f"({dev_version})"
    )

    current_branch = get_current_branch()

    if info.pyproject_file:
        quote = info.pyproject_version_quote
        update_line(
            info.pyproject_file,
            info.pyproject_version_line_number,
            f"version = {quote}{dev_version}{quote}",
        )

    if info.version_file:
        quote = info.version_quote
        update_line(
            info.version_file,
            info.version_line_number,
            f"__version__ = {quote}{dev_version}{quote}",
        )

    new_change_log_lines = [
        f"## {next_version} - unreleased\n\n",
        "In progress...\n\n",
    ]
    with info.change_log.open() as fp:
        lines = fp.readlines()
    lines = (
        lines[: info.change_log_line_number]
        + new_change_log_lines
        + lines[info.change_log_line_number :]
    )
    with info.change_log.open("w") as fp:
        fp.writelines(lines)

    commit_files = (info.pyproject_file, info.version_file, info.change_log)
    local(("git", "diff", *commit_files))

    if info.confirmation_required:
        confirm("Commit these changes?", abort_on_unconfirmed=True)
    else:
        printer.warning("Committing changes")

    msg = f"Resume development of {info.name} at {next_version}"
    msg = prompt("Commit message", default=msg)
    local(("git", "commit", commit_files, "-m", msg))

    local(("git", "checkout", current_branch))
