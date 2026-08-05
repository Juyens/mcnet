import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from mcnet.domain.models import LockedJar, LockFile, ServerManifest
from mcnet.errors import McnetError
from mcnet.storage import lock
from mcnet.storage.lock import LOCK_NAME

MANIFEST = ServerManifest(loader="paper", mc_version="1.21.4", port=25565)

LUCKPERMS = LockedJar(
    source="modrinth",
    version="5.4.140",
    filename="LuckPerms-Bukkit-5.4.140.jar",
    hash="4f3c",
    algorithm="sha512",
    url="https://cdn.modrinth.com/luckperms.jar",
    size=3_145_728,
)

VIAVERSION = LockedJar(
    source="hangar",
    version="5.2.1",
    filename="ViaVersion-5.2.1.jar",
    hash="9ab0",
    algorithm="sha512",
    url="https://hangarcdn.papermc.io/viaversion.jar",
    size=1_048_576,
)

PAPER = LockedJar(
    source="papermc",
    version="1.21.4-518",
    filename="paper-1.21.4-518.jar",
    hash="c0ff",
    algorithm="sha256",
    url="https://api.papermc.io/v2/projects/paper/paper-1.21.4-518.jar",
    size=52_428_800,
)

EXPECTED = LockFile(
    loader="paper",
    mc_version="1.21.4",
    server=PAPER,
    plugins={"luckperms": LUCKPERMS, "viaversion": VIAVERSION},
)


def write(tmp_path: Path, text: str) -> Path:
    (tmp_path / LOCK_NAME).write_text(text, encoding="utf-8")

    return tmp_path


def _jar_dict() -> dict[str, Any]:
    return {
        "source": "modrinth",
        "version": "5.4.140",
        "filename": "LuckPerms.jar",
        "hash": "4f3c",
        "algorithm": "sha512",
        "url": "https://cdn.modrinth.com/luckperms.jar",
        "size": 3_145_728,
    }


def _lock_json(**sections: Any) -> str:
    return json.dumps(
        {"schema": 1, "loader": "paper", "mc_version": "1.21.4", **sections}
    )


def test_a_missing_lock_starts_empty(tmp_path: Path) -> None:
    loaded = lock.load_lock(tmp_path, MANIFEST)

    assert loaded.plugins == {}
    assert loaded.loader == "paper"
    assert loaded.mc_version == "1.21.4"


def test_a_missing_lock_is_not_written(tmp_path: Path) -> None:
    lock.load_lock(tmp_path, MANIFEST)

    assert not (tmp_path / LOCK_NAME).exists()


def test_a_lock_survives_a_round_trip(tmp_path: Path) -> None:
    lock.save_lock(EXPECTED, tmp_path)

    assert lock.load_lock(tmp_path, MANIFEST) == EXPECTED


def test_the_same_lock_always_writes_the_same_bytes(tmp_path: Path) -> None:
    first = lock.save_lock(EXPECTED, tmp_path).read_text(encoding="utf-8")

    shuffled = LockFile(
        loader=EXPECTED.loader,
        mc_version=EXPECTED.mc_version,
        server=PAPER,
        plugins={"viaversion": VIAVERSION, "luckperms": LUCKPERMS},
    )

    assert lock.save_lock(shuffled, tmp_path).read_text(encoding="utf-8") == first


def test_a_lock_without_a_server_omits_the_key(tmp_path: Path) -> None:
    bare = LockFile(loader="paper", mc_version="1.21.4")

    saved = lock.save_lock(bare, tmp_path).read_text(encoding="utf-8")

    assert "server" not in json.loads(saved)
    assert lock.load_lock(tmp_path, MANIFEST).server is None


def test_a_malformed_server_entry_is_rejected(tmp_path: Path) -> None:
    folder = write(
        tmp_path,
        '{"schema": 1, "loader": "paper", "mc_version": "1.21.4",'
        ' "server": "paper-1.21.4.jar"}',
    )

    with pytest.raises(McnetError, match="malformed server entry"):
        lock.load_lock(folder, MANIFEST)


def test_a_server_missing_a_field_names_it(tmp_path: Path) -> None:
    entry = _jar_dict()
    del entry["url"]

    folder = write(tmp_path, _lock_json(server=entry))

    with pytest.raises(McnetError, match="missing 'url'"):
        lock.load_lock(folder, MANIFEST)


def test_a_size_that_is_not_a_number_is_rejected(tmp_path: Path) -> None:
    entry = _jar_dict() | {"size": "3 MB"}

    folder = write(tmp_path, _lock_json(plugins={"luckperms": entry}))

    with pytest.raises(McnetError, match="'size' must be a whole number"):
        lock.load_lock(folder, MANIFEST)


def test_broken_json_is_reported(tmp_path: Path) -> None:
    folder = write(tmp_path, "{ nope")

    with pytest.raises(McnetError, match="not valid JSON"):
        lock.load_lock(folder, MANIFEST)


def test_a_json_list_is_not_a_lock(tmp_path: Path) -> None:
    folder = write(tmp_path, "[1, 2]")

    with pytest.raises(McnetError, match="not a mcnet lock"):
        lock.load_lock(folder, MANIFEST)


def test_a_file_without_a_schema_key_is_rejected(tmp_path: Path) -> None:
    folder = write(tmp_path, '{"loader": "paper", "mc_version": "1.21.4"}')

    with pytest.raises(McnetError, match="not a mcnet lock"):
        lock.load_lock(folder, MANIFEST)


def test_a_newer_schema_asks_for_a_newer_mcnet(tmp_path: Path) -> None:
    folder = write(tmp_path, '{"schema": 99, "loader": "paper"}')

    with pytest.raises(McnetError, match="needs a newer mcnet"):
        lock.load_lock(folder, MANIFEST)


@pytest.mark.parametrize(
    "missing", ["source", "version", "filename", "hash", "algorithm", "url"]
)
def test_an_entry_missing_a_field_names_it(tmp_path: Path, missing: str) -> None:
    entry = _jar_dict()
    del entry[missing]

    folder = write(tmp_path, _lock_json(plugins={"luckperms": entry}))

    with pytest.raises(McnetError, match=f"missing '{missing}'"):
        lock.load_lock(folder, MANIFEST)


def test_a_jar_without_a_size_loads(tmp_path: Path) -> None:
    entry = _jar_dict()
    del entry["size"]

    folder = write(tmp_path, _lock_json(plugins={"luckperms": entry}))

    assert lock.load_lock(folder, MANIFEST).plugins["luckperms"].size is None


def test_an_unknown_size_is_left_out_of_the_file(tmp_path: Path) -> None:
    sizeless = LockFile(
        loader="paper",
        mc_version="1.21.4",
        plugins={"luckperms": replace(LUCKPERMS, size=None)},
    )

    saved = json.loads(lock.save_lock(sizeless, tmp_path).read_text(encoding="utf-8"))

    assert "size" not in saved["plugins"]["luckperms"]
    assert lock.load_lock(tmp_path, MANIFEST) == sizeless


def test_a_malformed_entry_is_rejected(tmp_path: Path) -> None:
    folder = write(
        tmp_path,
        '{"schema": 1, "loader": "paper", "mc_version": "1.21.4",'
        ' "plugins": {"luckperms": "5.4.140"}}',
    )

    with pytest.raises(McnetError, match="malformed entry for 'luckperms'"):
        lock.load_lock(folder, MANIFEST)


def test_a_lock_without_plugins_loads(tmp_path: Path) -> None:
    folder = write(tmp_path, '{"schema": 1, "loader": "paper", "mc_version": "1.21.4"}')

    assert lock.load_lock(folder, MANIFEST).plugins == {}


def test_removing_a_lock_that_is_not_there_is_fine(tmp_path: Path) -> None:
    assert lock.remove_lock(tmp_path) is None


def test_removing_a_lock_reports_the_path(tmp_path: Path) -> None:
    path = lock.save_lock(EXPECTED, tmp_path)

    assert lock.remove_lock(tmp_path) == path
    assert not path.exists()
