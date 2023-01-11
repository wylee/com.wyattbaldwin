from runcommands.commands import local
from runcommands.util import abort, confirm, printer

from .util import get_current_branch, print_step_header


def create_release_tag(info, merge):
    print_step_header(f"Tagging {info.name} release", info.version)

    current_branch = get_current_branch()

    printer.info("Source branch:", info.source_branch)

    if merge:
        printer.info("Target branch:", info.target_branch)
        local(("git", "checkout", info.target_branch), "\n")
    else:
        printer.info("Target branch:", info.source_branch, "\n")
        local(("git", "checkout", info.source_branch))

    printer.print()
    local("git log -1 --oneline")

    printer.print()
    if info.confirmation_required:
        confirmed = confirm("Tag this commit?")
    else:
        printer.warning("Tagging commit")
        confirmed = True

    if confirmed:
        msg = f"Release {info.name} {info.version}"
        local(("git", "tag", "-a", "-m", msg, info.tag_name))

    local(("git", "checkout", current_branch))

    if not confirmed:
        abort()
