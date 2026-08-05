import sys

import typer

from mcnet.cli.render import log
from mcnet.domain.models import Target
from mcnet.errors import McnetError
from mcnet.services import workspace


def confirm_name(name: str, *, refusal: str) -> None:
    """Make the user type the name, or abort saying nothing happened."""
    if typer.prompt(f"Type '{name}' to confirm") != name:
        raise McnetError(f"name does not match, {refusal}")


def select(
    names: list[str],
    *,
    action: str,
    yes: bool = False,
    default: bool = True,
) -> tuple[list[Target], list[str]]:
    """The servers to work on, and any name that turned out not to exist.

    Named ones win. Otherwise the folder we are standing in, if it is a
    server; otherwise whatever is under it, asking first when there is more
    than one, since 'do it everywhere' should be said out loud.
    """
    if names:
        return workspace.named(names)

    standing = workspace.here()

    if standing is not None:
        return [standing], []

    found = workspace.everything()

    if not found:
        raise McnetError(
            "no servers are managed here",
            hint="create one with 'mcnet server create', or cd into your network",
        )

    if len(found) == 1 or yes:
        return found, []

    return _confirm_all(found, action=action, default=default), []


def _confirm_all(found: list[Target], *, action: str, default: bool) -> list[Target]:
    example = " ".join(target.name for target in found[:2])
    named = f"name the ones you want:  mcnet {action} {example}"

    log.question(f"found {len(found)} servers here")
    log.question("  " + ", ".join(target.name for target in found))

    try:
        answered = _ask(f"{action} all of them?", default=default)
    except (typer.Abort, EOFError) as e:
        # Piped or scripted: Click would abort with a bare 'Aborted.', which
        # says nothing about how to get the job done.
        raise McnetError(
            "more than one server here and no terminal to ask with",
            hint=f"pass -y, or {named}",
        ) from e

    if answered:
        return found

    raise McnetError("nothing to do", hint=named)


def _ask(question: str, *, default: bool) -> bool:
    if not sys.stdin.isatty():
        raise EOFError(question)

    return typer.confirm(question, default=default, err=True)
