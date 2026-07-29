from mcnet.providers.modrinth.assembler import ModrinthAssembler


def test_keeps_only_releases_in_order() -> None:
    resources = [
        {"version": "26.2", "version_type": "release", "date": "", "major": True},
        {"version": "26.3-snapshot-1", "version_type": "snapshot", "date": "", "major": False},
        {"version": "26.1.2", "version_type": "release", "date": "", "major": False},
    ]

    assert ModrinthAssembler.to_release_versions(resources) == ["26.2", "26.1.2"]


def test_no_releases_gives_an_empty_list() -> None:
    resources = [
        {"version": "26.3-snapshot-1", "version_type": "snapshot", "date": "", "major": False},
    ]

    assert ModrinthAssembler.to_release_versions(resources) == []


def test_to_resolved_picks_the_primary_file() -> None:
    resource = {
        "version_number": "1.4.36",
        "files": [
            {
                "filename": "chunky-sources.jar",
                "url": "https://cdn.modrinth.com/sources.jar",
                "primary": False,
                "hashes": {"sha512": "aaa"},
            },
            {
                "filename": "chunky.jar",
                "url": "https://cdn.modrinth.com/chunky.jar",
                "primary": True,
                "hashes": {"sha512": "bbb"},
            },
        ],
    }

    resolved = ModrinthAssembler.to_resolved(resource)

    assert resolved is not None
    assert resolved.filename == "chunky.jar"
    assert resolved.url == "https://cdn.modrinth.com/chunky.jar"
    assert resolved.hash == "bbb"
    assert resolved.algorithm == "sha512"
    assert resolved.version == "1.4.36"


def test_to_resolved_returns_none_without_a_primary_file() -> None:
    resource = {
        "version_number": "1.0.0",
        "files": [
            {
                "filename": "chunky-sources.jar",
                "url": "https://cdn.modrinth.com/sources.jar",
                "primary": False,
                "hashes": {"sha512": "aaa"},
            },
        ],
    }

    assert ModrinthAssembler.to_resolved(resource) is None
