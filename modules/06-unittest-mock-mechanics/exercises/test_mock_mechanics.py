"""Exercise: AsyncMock, autospec, side_effect, mocker.

make ex M=06
"""

from __future__ import annotations

from unittest.mock import AsyncMock, create_autospec

import pytest

from shop.gateways.cache import RedisIdempotencyLock


async def test_asyncmock_for_the_idempotency_lock() -> None:
    """TODO: build an AsyncMock standing in for an IdempotencyLock. Configure its
    `.acquire` to return True when awaited, call `await mock.acquire("key-1",
    ttl_seconds=30)`, and assert both the return value AND that it was awaited with
    exactly those arguments (use the `_awaited_` family of assertions).
    """
    mock_idempotency_lock = AsyncMock()
    mock_idempotency_lock.acquire.return_value = True

    result = await mock_idempotency_lock.acquire("key-1", ttl_seconds=30)

    assert result is True
    mock_idempotency_lock.acquire.assert_awaited_once_with("key-1", ttl_seconds=30)


async def test_side_effect_simulates_lock_contention() -> None:
    """TODO: build an AsyncMock for `.acquire` whose side_effect returns False on the
    first call and True on the second (a caller retrying after someone else released
    the lock). Call it twice and assert on both results.
    """
    mock_acquire = AsyncMock(side_effect=[False, True])

    result_1 = await mock_acquire("key-1", ttl_seconds=30)
    assert result_1 is False

    # Retry
    result_2 = await mock_acquire("key-1", ttl_seconds=30)
    assert result_2 is True


async def test_autospec_on_redis_idempotency_lock_catches_a_bad_call() -> None:
    """TODO: build `create_autospec(RedisIdempotencyLock, instance=True)` and assert
    that calling `.acquire("key-1")` with NO `ttl_seconds` keyword argument raises
    TypeError (it's a required keyword-only argument on the real method).
    """
    mock_redis_lock = create_autospec(RedisIdempotencyLock, instance=True)

    with pytest.raises(TypeError):
        await mock_redis_lock.acquire("key-1")


async def test_mocker_patches_get_settings_and_cleans_up(mocker) -> None:
    """TODO: use `mocker.patch("shop.config.get_settings", return_value="patched")`,
    then import get_settings from shop.config and assert calling it returns
    "patched". No cleanup code needed -- that's the point; pytest-mock handles it.
    """
    mocker.patch("shop.config.get_settings", return_value="patched")

    from shop.config import get_settings

    assert get_settings() == "patched"
    # No cleanup code here -- and the next test in this file proves it wasn't needed:
