"""Exercise: AsyncMock, autospec, side_effect, mocker.

    make ex M=06
"""

from __future__ import annotations


async def test_asyncmock_for_the_idempotency_lock() -> None:
    """TODO: build an AsyncMock standing in for an IdempotencyLock. Configure its
    `.acquire` to return True when awaited, call `await mock.acquire("key-1",
    ttl_seconds=30)`, and assert both the return value AND that it was awaited with
    exactly those arguments (use the `_awaited_` family of assertions).
    """
    raise NotImplementedError("write this test")


async def test_side_effect_simulates_lock_contention() -> None:
    """TODO: build an AsyncMock for `.acquire` whose side_effect returns False on the
    first call and True on the second (a caller retrying after someone else released
    the lock). Call it twice and assert on both results.
    """
    raise NotImplementedError("write this test")


def test_autospec_on_redis_idempotency_lock_catches_a_bad_call() -> None:
    """TODO: build `create_autospec(RedisIdempotencyLock, instance=True)` and assert
    that calling `.acquire("key-1")` with NO `ttl_seconds` keyword argument raises
    TypeError (it's a required keyword-only argument on the real method).
    """
    raise NotImplementedError("write this test")


async def test_mocker_patches_get_settings_and_cleans_up(mocker) -> None:
    """TODO: use `mocker.patch("shop.config.get_settings", return_value="patched")`,
    then import get_settings from shop.config and assert calling it returns
    "patched". No cleanup code needed -- that's the point; pytest-mock handles it.
    """
    raise NotImplementedError("write this test")
