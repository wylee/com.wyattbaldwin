from runcommands.commands import local
from runcommands.util import confirm, printer, prompt

from .util import get_current_branch, print_step_header


def merge_to_target_branch(info):
    print_step_header(
        "Merging",
        info.dev_branch,
        "into",
        info.target_branch,
        "for release",
        info.version,
    )

    current_branch = get_current_branch()

    local(
        (
            "git",
            "log",
            "--oneline",
            "--reverse",
            f"{info.target_branch}..{info.dev_branch}",
        )
    )

    if info.confirmation_required:
        msg = (
            f"Merge these changes from {info.dev_branch} "
            f"into {info.target_branch} "
            f"for release {info.version}?"
        )
        confirm(msg, abort_on_unconfirmed=True)
    else:
        printer.warning(
            "Merging changes from",
            info.dev_branch,
            "into",
            info.target_branch,
            "for release",
            info.release,
        )

    local(("git", "checkout", info.target_branch))

    msg = f"Merge branch '{info.dev_branch}' for {info.name} release {info.version}"
    msg = prompt("Commit message", default=msg)
    local(("git", "merge", "--no-ff", info.dev_branch, "-m", msg))

    local(("git", "checkout", current_branch))
