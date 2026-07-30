import pytest

from mcnet.core.validation import MAX_NAME_LENGTH, is_version_shape, name_problem


@pytest.mark.parametrize(
    "value",
    ["26.1", "26.1.2", "1.21.4", "1.21.11", "0.0", "100.200.300"],
)
def test_accepts_version_shapes(value: str) -> None:
    assert is_version_shape(value)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty"),
        pytest.param("26", id="one-part"),
        pytest.param("26.1.2.3", id="four-parts"),
        pytest.param("26.x", id="letter"),
        pytest.param("1,21", id="comma"),
        pytest.param("latest", id="word"),
        pytest.param("26.3-snapshot-1", id="snapshot"),
        pytest.param(" 26.1", id="leading-space"),
        pytest.param("26.1 ", id="trailing-space"),
        pytest.param("26.1\n", id="trailing-newline"),
    ],
)
def test_rejects_invalid_versions(value: str) -> None:
    assert not is_version_shape(value)


@pytest.mark.parametrize(
    "value", ["survival", "lobby", "newtork123", "jup-idi", "mundito_123"]
)
def test_accepts_names(value: str) -> None:
    assert name_problem(value) is None


@pytest.mark.parametrize(
    "value",
    [
        # empty
        pytest.param("", id="empty"),
        # too long
        pytest.param("a" * (MAX_NAME_LENGTH + 1), id="one-over-limit"),
        # shape
        pytest.param("Survival", id="uppercase"),
        pytest.param("mi server", id="space"),
        pytest.param(" survival", id="leading-space"),
        pytest.param("survival ", id="trailing-space"),
        pytest.param("survival\n", id="trailing-newline"),
        pytest.param("-lobby", id="starts-with-hyphen"),
        pytest.param("_lobby", id="starts-with-underscore"),
        pytest.param("surv/ival", id="slash"),
        pytest.param("surv\\ival", id="backslash"),
        pytest.param("surv:ival", id="colon"),
        pytest.param("survival.old", id="dot"),
        pytest.param("señor", id="accented"),
        # reserved on Windows
        pytest.param("nul", id="nul"),
        pytest.param("con", id="con"),
        pytest.param("com1", id="com1"),
        pytest.param("lpt9", id="lpt9"),
    ],
)
def test_rejects_problematic_names(value: str):
    assert name_problem(value) is not None
