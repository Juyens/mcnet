from pathlib import Path

import pytest

from mcnet.domain.models import Plugin, ServerManifest
from mcnet.errors import McnetError
from mcnet.storage import manifest
from mcnet.storage.manifest import MANIFEST_NAME

GOLDEN = Path(__file__).parent / "fixtures" / "schema_v1.yaml"

EXPECTED = ServerManifest(
    loader="paper",
    mc_version="1.21.4",
    port=25565,
    plugins=[
        Plugin(source="modrinth", slug="luckperms"),
        Plugin(source="hangar", slug="viaversion"),
    ],
)


def write(tmp_path: Path, text: str) -> Path:
    (tmp_path / MANIFEST_NAME).write_text(text, encoding="utf-8")

    return tmp_path


def test_the_golden_manifest_loads(tmp_path: Path) -> None:
    folder = write(tmp_path, GOLDEN.read_text(encoding="utf-8"))

    assert manifest.load_manifest(folder) == EXPECTED


def test_saving_reproduces_the_golden_manifest(tmp_path: Path) -> None:
    path = manifest.save_manifest(EXPECTED, tmp_path)

    assert path.read_text(encoding="utf-8") == GOLDEN.read_text(encoding="utf-8")


def test_a_manifest_survives_a_round_trip(tmp_path: Path) -> None:
    manifest.save_manifest(EXPECTED, tmp_path)

    assert manifest.load_manifest(tmp_path) == EXPECTED


def test_a_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(McnetError, match=MANIFEST_NAME):
        manifest.load_manifest(tmp_path)


def test_an_empty_file_is_not_a_manifest(tmp_path: Path) -> None:
    folder = write(tmp_path, "")

    with pytest.raises(McnetError, match="not a mcnet manifest"):
        manifest.load_manifest(folder)


def test_a_yaml_list_is_not_a_manifest(tmp_path: Path) -> None:
    folder = write(tmp_path, "- lobby\n- survival\n")

    with pytest.raises(McnetError, match="not a mcnet manifest"):
        manifest.load_manifest(folder)


def test_a_file_without_a_schema_key_is_rejected(tmp_path: Path) -> None:
    folder = write(tmp_path, "loader: paper\nmc_version: 1.21.4\nport: 25565\n")

    with pytest.raises(McnetError, match="not a mcnet manifest"):
        manifest.load_manifest(folder)


def test_a_non_numeric_schema_is_rejected(tmp_path: Path) -> None:
    folder = write(tmp_path, "schema: one\nloader: paper\n")

    with pytest.raises(McnetError, match="not a mcnet manifest"):
        manifest.load_manifest(folder)


def test_a_newer_schema_asks_for_a_newer_mcnet(tmp_path: Path) -> None:
    folder = write(tmp_path, "schema: 99\nloader: paper\n")

    with pytest.raises(McnetError, match="needs a newer mcnet"):
        manifest.load_manifest(folder)


def test_an_unknown_older_schema_is_rejected(tmp_path: Path) -> None:
    folder = write(tmp_path, "schema: 0\nloader: paper\n")

    with pytest.raises(McnetError, match="unknown schema"):
        manifest.load_manifest(folder)


@pytest.mark.parametrize("missing", ["loader", "mc_version", "port"])
def test_a_missing_field_names_itself(tmp_path: Path, missing: str) -> None:
    fields = {"loader": "paper", "mc_version": "1.21.4", "port": "25565"}
    del fields[missing]

    body = "".join(f"{key}: {value}\n" for key, value in fields.items())
    folder = write(tmp_path, f"schema: 1\n{body}")

    with pytest.raises(McnetError, match=f"missing '{missing}'"):
        manifest.load_manifest(folder)


def test_a_manifest_without_plugins_loads(tmp_path: Path) -> None:
    folder = write(tmp_path, "schema: 1\nloader: paper\nmc_version: 1.21.4\nport: 1\n")

    assert manifest.load_manifest(folder).plugins == []


def test_a_malformed_plugin_entry_is_rejected(tmp_path: Path) -> None:
    folder = write(
        tmp_path,
        "schema: 1\nloader: paper\nmc_version: 1.21.4\nport: 1\nplugins:\n- lucky\n",
    )

    with pytest.raises(McnetError, match="malformed plugin entry"):
        manifest.load_manifest(folder)


def test_a_plugin_missing_its_slug_is_rejected(tmp_path: Path) -> None:
    folder = write(
        tmp_path,
        "schema: 1\nloader: paper\nmc_version: 1.21.4\nport: 1\n"
        "plugins:\n- source: modrinth\n",
    )

    with pytest.raises(McnetError, match="missing 'slug'"):
        manifest.load_manifest(folder)
