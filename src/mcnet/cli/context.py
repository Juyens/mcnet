import typer

from mcnet.services.session import Session


def attach(ctx: typer.Context) -> None:
    ctx.obj = ctx.with_resource(Session())


def session(ctx: typer.Context) -> Session:
    """Typed access to what attach() wired up."""
    if not isinstance(ctx.obj, Session):
        raise RuntimeError("providers are missing, attach() never ran")

    return ctx.obj
