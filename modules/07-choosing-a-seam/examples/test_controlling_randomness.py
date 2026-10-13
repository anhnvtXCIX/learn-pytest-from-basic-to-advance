"""The pytest-randomly reseeding trap (found for real while writing module 03), and
the dependency-injection fix.
"""

from __future__ import annotations

import random

import pytest


def pick_discount_code_global(length: int = 6) -> str:
    """Reaches directly into the global `random` module -- hard to control in a test
    in THIS repo specifically, because pytest-randomly reseeds `random` right before
    every test's call phase.
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(random.choice(alphabet) for _ in range(length))


@pytest.fixture
def seeded_global_random() -> None:
    random.seed(1234)


def test_seeding_random_in_the_test_body_works() -> None:
    """Seeding inside the test body is fine. pytest-randomly reseeds in its
    `pytest_runtest_call` hook, which runs BEFORE the test function starts, so this
    seed lands afterwards and wins. (Verified: same code every run, with and without
    `-p no:randomly`.) The trap is only for seeding that happens EARLIER -- see below.
    """
    random.seed(1234)
    first = pick_discount_code_global()
    random.seed(1234)
    second = pick_discount_code_global()

    assert first == second


def test_seeding_random_in_a_fixture_is_overwritten_by_pytest_randomly(
    seeded_global_random: None, request: pytest.FixtureRequest
) -> None:
    """The actual trap: a fixture's `random.seed(1234)` runs in the setup phase, then
    pytest-randomly reseeds right before the call phase and silently discards it.
    The test body therefore does NOT see the fixture's seed.

    Only meaningful with the plugin active; with `-p no:randomly` the fixture's seed
    survives, so there is nothing to demonstrate and we skip.
    """
    if not request.config.pluginmanager.hasplugin("randomly"):
        pytest.skip("pytest-randomly is disabled, so the fixture's seed survives")

    code = pick_discount_code_global()
    what_seed_1234_would_give = InjectedRandomSource(random.Random(1234)).pick_discount_code()

    # 26**-6 chance of a false failure by coincidence -- negligible.
    assert code != what_seed_1234_would_give


class InjectedRandomSource:
    """The fix: accept a `random.Random` instance instead of touching the global
    module. A test can hand this a Random seeded however it likes, completely
    independent of pytest-randomly's global reseeding, because this Random instance
    is never touched by pytest-randomly at all.
    """

    def __init__(self, source: random.Random) -> None:
        self._source = source

    def pick_discount_code(self, length: int = 6) -> str:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "".join(self._source.choice(alphabet) for _ in range(length))


def test_injected_random_source_is_fully_deterministic() -> None:
    generator = InjectedRandomSource(random.Random(1234))

    first = generator.pick_discount_code()

    # A FRESH Random(1234) reproduces the exact same sequence -- unaffected by
    # whatever pytest-randomly did to the global `random` module in between.
    second = InjectedRandomSource(random.Random(1234)).pick_discount_code()

    assert first == second
