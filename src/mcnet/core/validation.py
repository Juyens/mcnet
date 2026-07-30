import re

_VERSION = re.compile(r"^\d+\.\d+(\.\d+)?\Z")

_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*\Z")

MAX_NAME_LENGTH = 32

_RESERVED_NAMES = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }
)


def is_version_shape(value: str) -> bool:
    return _VERSION.match(value) is not None


def name_problem(value: str) -> str | None:
    if not value:
        return "the name cannot be empty"

    if len(value) > MAX_NAME_LENGTH:
        return f"the name cannot be longer than {MAX_NAME_LENGTH} characters"

    if not _NAME.match(value):
        return "use lowercase letters, numbers, '-' and '_', starting with a letter or number"

    if value in _RESERVED_NAMES:
        return f"'{value}' is a reserved name on Windows"

    return None
