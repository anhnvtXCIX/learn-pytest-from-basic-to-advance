"""Reference solution for exercises/test_mock_mechanics.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, create_autospec

import pytest

from shop.gateways.cache import RedisIdempotencyLock


async def test_asyncmock_for_the_idempotency_lock() -> None:
    mock_lock = AsyncMock()
    mock_lock.acquire.return_value = True

    result = await mock_lock.acquire("key-1", ttl_seconds=30)

    assert result is True
    mock_lock.acquire.assert_awaited_once_with("key-1", ttl_seconds=30)


async def test_side_effect_simulates_lock_contention() -> None:
    mock_acquire = AsyncMock(side_effect=[False, True])

    first = await mock_acquire("key-1", ttl_seconds=30)
    second = await mock_acquire("key-1", ttl_seconds=30)

    assert first is False
    assert second is True


def test_autospec_on_redis_idempotency_lock_catches_a_bad_call() -> None:
    mock_lock = create_autospec(RedisIdempotencyLock, instance=True)

    with pytest.raises(TypeError):
        mock_lock.acquire("key-1")


async def test_mocker_patches_get_settings_and_cleans_up(mocker) -> None:
    mocker.patch("shop.config.get_settings", return_value="patched")

    from shop.config import get_settings

    assert get_settings() == "patched"
