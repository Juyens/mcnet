import hashlib
from pathlib import Path


def file_matches(path: Path, expected_hash: str, algorithm: str) -> bool:
    if not path.exists():
        return False

    digest = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest() == expected_hash
