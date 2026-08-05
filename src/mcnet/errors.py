class McnetError(Exception):
    """Base for all expected mcnet errors."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


class NotFoundError(McnetError):
    """The resource is not there, as opposed to being out of reach.

    Providers lean on this to tell 'no build for that version' apart from
    'the API is down', which mean very different things to the caller.
    """
