"""`autouse=True`: applies to every test in this file without being named as a
parameter. Notice that neither test below mentions `_reset_audit_log` -- that's
exactly the readability cost autouse trades for convenience; reserve it for
genuinely cross-cutting concerns like "reset shared state before every test," never
for "convenient" domain test data a reader would expect to see requested explicitly.

(This module's first draft tried to demonstrate autouse by auto-seeding Python's
`random` module -- and got flaky, different-every-run results. Root cause: this
repo's `pytest-randomly` plugin reseeds the global `random` state itself immediately
before each test's call phase, which clobbers a fixture's own `random.seed(...)`
regardless of what the fixture does during setup. Real lesson, wrong module -- see
`modules/07-choosing-a-seam/README.md` for controlling randomness the way this repo
actually recommends: dependency injection, not global mutable state.)
"""

from __future__ import annotations

import pytest

_audit_log: list[str] = []


def record(event: str) -> None:
    _audit_log.append(event)


@pytest.fixture(autouse=True)
def _reset_audit_log() -> None:
    _audit_log.clear()


def test_log_starts_empty() -> None:
    assert _audit_log == []
    record("first")
    assert _audit_log == ["first"]


def test_log_was_reset_before_this_test_too() -> None:
    """If `_reset_audit_log` weren't autouse (or didn't run before every test), this
    could see `["first"]` left over from the test above. It doesn't -- and that's
    true no matter which of these two tests pytest-randomly happens to run first.
    """
    assert _audit_log == []
