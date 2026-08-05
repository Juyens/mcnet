import pytest

from mcnet.cli.render.progress import MIN_BAR_SIZE, shows_bar

MEGABYTE = 1024 * 1024


@pytest.mark.parametrize("size", [1, 512 * 1024, MEGABYTE, 5 * MEGABYTE])
def test_a_small_file_gets_no_bar_of_its_own(size: int) -> None:
    """A typical plugin lands in under a second: a bar would only flicker."""
    assert not shows_bar(size)


@pytest.mark.parametrize("size", [MIN_BAR_SIZE, 19 * MEGABYTE, 54 * MEGABYTE])
def test_anything_worth_waiting_for_gets_one(size: int) -> None:
    assert shows_bar(size)


def test_an_unknown_size_gets_one() -> None:
    """Purpur publishes no size and ships 54MB, so absence proves nothing."""
    assert shows_bar(None)
