from typing import Annotated

import typer

from mcnet.cli import context, prompts
from mcnet.cli.handler import handle
from mcnet.cli.render import log, progress
from mcnet.domain.models import Target
from mcnet.domain.results import ServerBuild
from mcnet.process import Java
from mcnet.services import build as service
from mcnet.services import sync as syncing

EULA_URL = "https://aka.ms/MinecraftEULA"


@handle
def run(
    ctx: typer.Context,
    names: Annotated[
        list[str] | None,
        typer.Argument(help="Servers to build, or every one here"),
    ] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Start again even if already generated")
    ] = False,
    accept_eula: Annotated[
        bool,
        typer.Option("--accept-eula", help=f"Agree to the Minecraft EULA ({EULA_URL})"),
    ] = False,
    jobs: Annotated[
        int,
        typer.Option("--jobs", "-j", help="Downloads to run at once", min=1, max=32),
    ] = syncing.DEFAULT_WORKERS,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Do not ask before building all")
    ] = False,
):
    """Make each server runnable: settings, launchers, and a first start."""
    current = context.session(ctx)

    # Building everything means minutes and gigabytes, so the default answer
    # is no, unlike sync where saying yes costs nothing.
    targets, unknown = prompts.select(
        names or [], action="build", yes=yes, default=False
    )

    for name in unknown:
        log.err(f"no server named '{name}'")

    if not targets:
        raise typer.Exit(code=1)

    with progress.RichSink() as sink:
        syncing.sync(
            targets,
            current.providers,
            current.downloader,
            current.cache,
            workers=jobs,
            sink=sink,
        )

    result = service.build(
        targets,
        Java(),
        eula_accepted=accept_eula or _agreed(service.needs_eula(targets)),
        force=force,
        watch=_watch,
    )

    for server in result.servers:
        _report(server)

    if result.failed:
        raise typer.Exit(code=1)


def _agreed(pending: list[Target]) -> bool:
    """Ask once for the whole run, and only when somebody still has to."""
    if not pending:
        return False

    log.question("a Minecraft server cannot start until you accept the EULA")
    log.question(f"  {EULA_URL}")

    return prompts.confirm("do you accept it?", default=False)


def _watch(name: str, line: str) -> None:
    for marker in ("Preparing level", "Preparing spawn area", "Done ("):
        if marker in line:
            log.detail(f"{name}: {line.split(']: ')[-1]}")
            return


def _report(server: ServerBuild) -> None:
    if server.problem is not None:
        log.warn(f"{server.name}: {server.problem}")
    elif server.eula_pending:
        log.warn(f"{server.name}: waiting on the EULA")
    elif server.generated:
        log.ok(f"{server.name} is built")
    elif server.skipped:
        log.ok(f"{server.name} is up to date")

    if server.written:
        log.detail("wrote " + ", ".join(server.written))

    if server.problem is not None and server.written:
        log.hint("the files are there, only the first start is missing")
