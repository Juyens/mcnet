import hashlib
from pathlib import Path

from mcnet.errors import McnetError

CHUNK = 65536


def new_hasher(algorithm: str) -> hashlib._Hash:
    try:
        return hashlib.new(algorithm)
    except ValueError as e:
        raise McnetError(f"unknown hash algorithm: {algorithm}") from e


def digest_file(path: Path, algorithm: str) -> str:
    """Hash a file in chunks, so a big jar never lands in memory."""
    hasher = new_hasher(algorithm)

    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            hasher.update(chunk)

    return hasher.hexdigest()


def file_matches(path: Path, expected: str, algorithm: str) -> bool:
    """True when the file is already on disk with the hash we expect."""
    if not path.exists():
        return False

    return digest_file(path, algorithm) == expected
