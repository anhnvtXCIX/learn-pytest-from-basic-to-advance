"""Three tests with names deliberately chosen to prove conftest.py's `items.sort()`
runs, and that its effect survives pytest-randomly's shuffle rather than being
undone by it. Run:
    uv run pytest modules/13-pytest-plugins/examples/test_hook_ordering.py --collect-only -q
a few times (different random seeds each time) and check `test_z_runs_last` is
always last, while the other two swap freely -- proof the shuffle DID happen, and
that the sort still wins.
"""

from __future__ import annotations


def test_a_something() -> None:
    assert True


def test_m_something_else() -> None:
    assert True


def test_z_runs_last() -> None:
    assert True
