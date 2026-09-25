"""`yield` fixtures, `request.addfinalizer`, and proof that teardown runs even when
the test fails -- via `pytester`, pytest's own "run an isolated pytest session and
assert on its outcome" tool. This sidesteps the fact that we can't otherwise prove
"ran after a *failing* test" without depending on test order in our own suite.
"""

from __future__ import annotations

import pytest


class FakeConnection:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def connection():
    conn = FakeConnection()
    yield conn
    conn.close()  # runs after the test returns, success or failure


def test_connection_is_open_during_the_test(connection: FakeConnection) -> None:
    assert connection.closed is False


@pytest.fixture
def resource_pool(request: pytest.FixtureRequest):
    """`request.addfinalizer` instead of `yield`: useful when a fixture creates a
    *variable number* of things per test and each needs its own cleanup, which a
    single `yield` can't express as naturally as a loop of `addfinalizer` calls.
    """
    created: list[FakeConnection] = []

    def _get_connection() -> FakeConnection:
        conn = FakeConnection()
        created.append(conn)
        request.addfinalizer(conn.close)
        return conn

    return _get_connection


def test_resource_pool_hands_out_independent_connections(resource_pool) -> None:
    first = resource_pool()
    second = resource_pool()

    assert first is not second
    assert first.closed is False
    assert second.closed is False
    # Both will be closed via their registered finalizers once this test returns --
    # nothing left to assert here; see the pytester-based test below for proof that
    # this kind of teardown genuinely fires even after a failure.


def test_yield_teardown_runs_even_when_the_test_fails(pytester: pytest.Pytester) -> None:
    """Requires `pytest_plugins = ["pytester"]` in the repo's root conftest.py.

    Two deliberate choices here, both found by actually running this and hitting a
    real failure while writing it (not assumed up front):

    - `runpytest_subprocess()`, not `runpytest()`. The plain in-process form shares
      this outer process's global state -- including the `warnings` filter stack --
      with the inner run. Since this repo's `filterwarnings = ["error"]` is already
      active in the outer test that's calling `pytester`, an in-process inner run
      hits pytest-asyncio's own internal `warnings.warn(...)` during its startup and
      that gets promoted to an exception too, crashing pytest itself
      (`INTERNALERROR`) before the inner test even starts. A subprocess has its own
      fresh interpreter and warnings state, so it doesn't inherit any of that.
    - `-p no:randomly` on the inner run, so pytest-randomly (active in the outer
      suite, and inherited by a subprocess since it's installed in this same
      environment) doesn't shuffle order *inside* the throwaway file below -- this
      specific assertion needs test 1 to run before test 2.
    """
    pytester.makepyfile(
        """
        import pytest

        teardown_ran = []

        @pytest.fixture
        def resource():
            yield "value"
            teardown_ran.append(True)

        def test_1_fails_on_purpose(resource):
            assert resource == "value"
            assert False, "deliberate failure, to prove teardown still runs"

        def test_2_teardown_already_happened():
            assert teardown_ran == [True]
        """
    )

    result = pytester.runpytest_subprocess("-p", "no:randomly")

    result.assert_outcomes(failed=1, passed=1)
