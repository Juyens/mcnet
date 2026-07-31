class McnetError(Exception):
    """Base for all expected mcnet errors."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint
