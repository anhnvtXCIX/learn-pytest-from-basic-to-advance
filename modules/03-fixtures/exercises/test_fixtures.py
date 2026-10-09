"""Exercise: scopes, yield teardown, factory fixtures, tmp_path.

make ex M=03
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable

import pytest

from shop.domain.models import OrderLine

# --- Exercise 1: module scope -----------------------------------------------------

_shared_counter_calls = 0


@pytest.fixture(scope="module")
def shared_counter() -> int:
    # TODO: make this increment `_shared_counter_calls` (use `global`) and return it,
    # the same pattern as examples/test_fixture_scopes.py's module_scoped_resource.
    global _shared_counter_calls
    _shared_counter_calls += 1

    return _shared_counter_calls


@pytest.fixture(scope="module", autouse=True)
def _verify_shared_counter_ran_once():
    yield
    # TODO: assert _shared_counter_calls == 1 -- two tests below use `shared_counter`,
    # but module scope means its body should only ever run ONCE for the whole file.
    # This is the order-independent proof pattern from the examples: a module-scoped
    # fixture's teardown runs after the LAST test in this file, regardless of which
    # order pytest-randomly chose to run them in.
    assert _shared_counter_calls == 1


def test_shared_counter_first_use(shared_counter: int) -> None:
    assert shared_counter == 1


def test_shared_counter_second_use(shared_counter: int) -> None:
    # TODO: assert the value is the SAME as the first test saw -- proof of reuse.
    assert shared_counter == 1


# --- Exercise 2: yield teardown ----------------------------------------------------


class SpyFile:
    def __init__(self) -> None:
        self.open = True

    def close(self) -> None:
        self.open = False


@pytest.fixture
def spy_file():
    # TODO: create a SpyFile, yield it, then close it after the yield.
    spy = SpyFile()
    yield spy
    spy.close()


def test_spy_file_is_open_during_the_test(spy_file: SpyFile) -> None:
    assert spy_file.open is True


# --- Exercise 3: factory-as-fixture -------------------------------------------------


@pytest.fixture
def make_line() -> Callable[..., OrderLine]:
    # TODO: return a callable `_make(*, product_id=1, quantity=1, unit_price_cents=100)`
    # that builds and returns an OrderLine with those defaults, overridable by keyword.
    def _make(*, product_id: int = 1, quantity: int = 1, unit_price_cents: int = 100) -> OrderLine:
        return OrderLine(product_id, quantity, unit_price_cents)

    return _make


def test_make_line_default(make_line: Callable[..., OrderLine]) -> None:
    line = make_line()
    assert line.quantity == 1
    assert line.unit_price_cents == 100


def test_make_line_override(make_line: Callable[..., OrderLine]) -> None:
    # TODO: build a line with quantity=5 using make_line, and assert line.quantity == 5
    # and that line.unit_price_cents is still the default (100).
    line = make_line(quantity=5)

    assert line.quantity == 5
    assert line.unit_price_cents == 100


# --- Exercise 4: tmp_path -----------------------------------------------------------


def test_write_and_read_back_a_file(tmp_path: pathlib.Path) -> None:
    # TODO: write the text "hello" to a file named "note.txt" inside tmp_path, then
    # read it back and assert it round-trips.
    file_path = tmp_path / "note.txt"

    file_path.write_text("hello")

    assert file_path.exists()

    data = file_path.read_text()

    assert data == "hello"
