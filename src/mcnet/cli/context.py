import typer

from mcnet.providers.http import Http
from mcnet.providers.registry import Providers
from mcnet.storage.paths import cache_dir

USER_AGENT = "juyens/mcnet (joseph.juliuscb@gmail.com)"


def attach(ctx: typer.Context) -> None:
    """Wire the providers into ctx, closing the client when the command ends."""
    http = Http(USER_AGENT, cache_dir())
    ctx.call_on_close(http.close)

    ctx.obj = Providers(http)


def providers(ctx: typer.Context) -> Providers:
    """Typed access to what attach() wired up."""
    if not isinstance(ctx.obj, Providers):
        raise RuntimeError("providers are missing, attach() never ran")

    return ctx.obj
