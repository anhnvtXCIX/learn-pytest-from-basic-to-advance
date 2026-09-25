"""The pytest-randomly reseeding trap (found for real while writing module 03), and
the dependency-injection fix.
"""

from __future__ import annotations

import random


def pick_discount_code_global(length: int = 6) -> str:
    """Reaches directly into the global `random` module -- hard to control in a test
    in THIS repo specifically, because pytest-randomly reseeds `random` right before
    every test's call phase.
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(random.choice(alphabet) for _ in range(length))


def test_seeding_random_in_the_test_body_does_not_reliably_control_it() -> None:
    """This demonstrates the trap, it does not prove determinism -- read it as "here
    is what does NOT work," not as a pattern to copy. Because pytest-randomly's
    per-test reseed happens at the same point in the test lifecycle as this, the
    actual value pick_discount_code_global() returns here varies run to run (try
    running this file a few times with -p no:randomly vs without it and compare).
    """
    random.seed(1234)
    code = pick_discount_code_global()

    assert len(code) == 6
    assert code.isalpha()
    # Deliberately NOT asserting a specific code value here -- see the docstring.


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
