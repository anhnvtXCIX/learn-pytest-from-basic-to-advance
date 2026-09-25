"""Reference solution for exercises/test_fixtures.py."""

from __future__ import annotations

import pathlib
from collections.abc import Callable

import pytest

from shop.domain.models import OrderLine

# --- Exercise 1: module scope -----------------------------------------------------

_shared_counter_calls = 0


@pytest.fixture(scope="module")
def shared_counter() -> int:
    global _shared_counter_calls
    _shared_counter_calls += 1
    return _shared_counter_calls


@pytest.fixture(scope="module", autouse=True)
def _verify_shared_counter_ran_once():
    yield
    assert _shared_counter_calls == 1  # ran once total, despite two tests using it


def test_shared_counter_first_use(shared_counter: int) -> None:
    assert shared_counter == 1


def test_shared_counter_second_use(shared_counter: int) -> None:
    assert shared_counter == 1


# --- Exercise 2: yield teardown ----------------------------------------------------


class SpyFile:
    def __init__(self) -> None:
        self.open = True

    def close(self) -> None:
        self.open = False


@pytest.fixture
def spy_file():
    file = SpyFile()
    yield file
    file.close()


def test_spy_file_is_open_during_the_test(spy_file: SpyFile) -> None:
    assert spy_file.open is True


# --- Exercise 3: factory-as-fixture -------------------------------------------------


@pytest.fixture
def make_line() -> Callable[..., OrderLine]:
    def _make(*, product_id: int = 1, quantity: int = 1, unit_price_cents: int = 100) -> OrderLine:
        return OrderLine(
            product_id=product_id, quantity=quantity, unit_price_cents=unit_price_cents
        )

    return _make


def test_make_line_default(make_line: Callable[..., OrderLine]) -> None:
    line = make_line()
    assert line.quantity == 1
    assert line.unit_price_cents == 100


def test_make_line_override(make_line: Callable[..., OrderLine]) -> None:
    line = make_line(quantity=5)
    assert line.quantity == 5
    assert line.unit_price_cents == 100


# --- Exercise 4: tmp_path -----------------------------------------------------------


def test_write_and_read_back_a_file(tmp_path: pathlib.Path) -> None:
    note_path = tmp_path / "note.txt"

    note_path.write_text("hello")

    assert note_path.read_text() == "hello"
