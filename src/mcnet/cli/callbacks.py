import difflib

import typer

from mcnet.core import error, log, validation
from mcnet.providers import get_http
from mcnet.providers.minecraft import MinecraftVersions


def validate_version(ctx: typer.Context, value: str) -> str:
    if ctx.resilient_parsing:
        return value

    if not validation.is_version_shape(value):
        raise typer.BadParameter(f"'{value}' is not a Minecraft version")

    try:
        known = MinecraftVersions(get_http()).releases()
    except error.McnetError:
        log.warn(f"could not verify {value} with Modrinth, continuing anyway")
        return value

    if value in known:
        return value

    message = f"Minecraft {value} does not exist"

    close = difflib.get_close_matches(value, known, n=1)
    if close:
        message = f"{message}. Did you mean {close[0]}?"

    raise typer.BadParameter(message)
