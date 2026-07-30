import functools
from collections.abc import Callable
from typing import Any

import typer

from mcnet.core import log
from mcnet.core.error import McnetError


def handle(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Turn McnetError into a clean message and exit code 1."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except McnetError as e:
            log.err(str(e))

            if e.hint:
                log.hint(e.hint)

            raise typer.Exit(code=1) from e

    return wrapper
