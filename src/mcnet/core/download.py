import hashlib
from pathlib import Path

import httpx

from mcnet.core import errors


def download(url: str, hash: str, algorithm: str, filename: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    hash_algorithm = hashlib.new(algorithm)

    with httpx.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        with tmp.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
                hash_algorithm.update(chunk)

    if hash_algorithm.hexdigest() != hash:
        tmp.unlink()
        raise errors.McnetError(f"hash mismatch for {filename}")

    tmp.replace(dest)
