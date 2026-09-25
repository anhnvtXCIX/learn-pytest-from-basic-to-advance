"""Fixture scopes, proven with assertions rather than "trust me" -- and proven in an
order-independent way, because this suite runs with pytest-randomly (module 00).

The trick: a MODULE-scoped fixture's teardown always runs after the last test in
this file finishes, whichever test that happens to be. That's what lets
`_verify_scope_behavior_after_all_tests_ran` check call counts reliably regardless
of what order pytest-randomly picked.

Also try:
    uv run pytest modules/03-fixtures/examples/test_fixture_scopes.py --setup-show
to *see* each fixture's setup/teardown as it happens.
"""

from __future__ import annotations

import pytest

_function_scope_calls = 0
_module_scope_calls = 0


@pytest.fixture
def function_scoped_resource() -> int:
    """scope="function" (pytest's default) -- this body runs once for EVERY test
    that requests it.
    """
    global _function_scope_calls
    _function_scope_calls += 1
    return _function_scope_calls


@pytest.fixture(scope="module")
def module_scoped_resource() -> int:
    """scope="module" -- this body runs ONCE for the whole file. Every test below
    that requests it gets back the exact same return value.
    """
    global _module_scope_calls
    _module_scope_calls += 1
    return _module_scope_calls


@pytest.fixture(scope="module", autouse=True)
def _verify_scope_behavior_after_all_tests_ran():
    """`autouse=True` so this runs without any test naming it explicitly. NOTE: if
    you add a fourth test below that uses `function_scoped_resource`, update the
    `== 3` here to match -- this assertion is intentionally exact, not `>=`, so it
    actually proves something.
    """
    yield
    assert _function_scope_calls == 3, "one call per test that requested it"
    assert _module_scope_calls == 1, "one call total, shared across every test"


def test_a_requests_both_resources(
    function_scoped_resource: int, module_scoped_resource: int
) -> None:
    assert module_scoped_resource == 1


def test_b_requests_both_resources(
    function_scoped_resource: int, module_scoped_resource: int
) -> None:
    # Same value test_a saw, whichever of the two actually ran first -- proof of reuse.
    assert module_scoped_resource == 1


def test_c_requests_both_resources(
    function_scoped_resource: int, module_scoped_resource: int
) -> None:
    assert module_scoped_resource == 1
