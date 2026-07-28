import re

_VERSION = re.compile(r"^\d+\.\d+(\.\d+)?$")


def is_version_shape(value: str) -> bool:
    return _VERSION.match(value) is not None
