import pytest

from mcnet.core.validation import is_version_shape, name_problem


@pytest.mark.parametrize(
    "value",
    ["26.1", "26.1.2", "1.21.4", "1.21.11"],
)
def test_accepts_release_shapes(value: str) -> None:
    assert is_version_shape(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "26",
        "26.x",
        "26.1.2.3",
        "1,21",
        "latest",
        "26.3-snapshot-1",
        " 26.1",
    ],
)
def test_rejects_anything_else(value: str) -> None:
    assert not is_version_shape(value)


@pytest.mark.parametrize("value", ["survival", "lobby-2", "mi_red", "s"])
def test_accepts_simple_names(value: str) -> None:
    assert name_problem(value) is None


@pytest.mark.parametrize(
    "value",
    ["", "Survival", "mi server", "-lobby", "surv/ival", "nul", "com1", "a" * 33],
)
def test_rejects_problematic_names(value: str) -> None:
    assert name_problem(value) is not None
