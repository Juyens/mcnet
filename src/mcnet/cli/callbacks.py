import difflib

import typer

from mcnet.core import error, log, validation
from mcnet.providers import registry


def validate_version(ctx: typer.Context, value: str) -> str:
    if ctx.resilient_parsing:
        return value

    if not validation.is_version_shape(value):
        raise typer.BadParameter(f"'{value}' is not a Minecraft version")

    modrinth_api = registry.get_providers().modrinth

    try:
        known_versions = modrinth_api.game_versions()
    except error.McnetError:
        log.warn(f"could not verify {value} with Modrinth, continuing anyway")
        return value

    if value in known_versions:
        return value

    message = f"Minecraft {value} does not exist"

    close = difflib.get_close_matches(value, known_versions, n=1)
    if close:
        message = f"{message}. Did you mean {close[0]}?"

    raise typer.BadParameter(message)


def validate_name(ctx: typer.Context, value: str) -> str:
    if ctx.resilient_parsing:
        return value

    problem = validation.name_problem(value)
    if problem is not None:
        raise typer.BadParameter(problem)

    return value
