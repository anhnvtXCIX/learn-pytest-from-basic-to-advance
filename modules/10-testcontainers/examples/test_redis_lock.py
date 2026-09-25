"""`RedisIdempotencyLock` against a REAL Redis. Module 05's `FakeIdempotencyLock`
(a plain Python `set`) is behaviorally correct for single-process tests, but it
cannot tell you anything about TTL expiry or cross-connection visibility -- both are
Redis-specific behaviors that only a real Redis can honestly confirm.
"""

from __future__ import annotations

import asyncio

import pytest
import redis.asyncio as redis

from shop.gateways.cache import RedisIdempotencyLock

pytestmark = pytest.mark.docker


@pytest.fixture
async def redis_client(redis_url: str):
    client = redis.from_url(redis_url)
    yield client
    await client.flushdb()
    await client.aclose()


async def test_second_acquire_of_the_same_key_fails_while_the_first_holds_it(
    redis_client: redis.Redis,
) -> None:
    lock = RedisIdempotencyLock(redis_client)

    first = await lock.acquire("order-key-1", ttl_seconds=30)
    second = await lock.acquire("order-key-1", ttl_seconds=30)

    assert first is True
    assert second is False  # someone else already holds it


async def test_release_lets_a_new_acquire_succeed(redis_client: redis.Redis) -> None:
    lock = RedisIdempotencyLock(redis_client)
    await lock.acquire("order-key-2", ttl_seconds=30)

    await lock.release("order-key-2")
    reacquired = await lock.acquire("order-key-2", ttl_seconds=30)

    assert reacquired is True


async def test_ttl_expiry_lets_a_new_acquire_succeed_without_an_explicit_release(
    redis_client: redis.Redis,
) -> None:
    """The scenario a fake can't prove: a caller crashes after acquiring the lock and
    never calls release() -- real production behavior a unit test with a Python
    `set`-backed fake would have to fake the passage of time for. Here, real time
    (a short TTL) actually passes.
    """
    lock = RedisIdempotencyLock(redis_client)
    await lock.acquire("order-key-3", ttl_seconds=1)

    await asyncio.sleep(1.2)
    reacquired = await lock.acquire("order-key-3", ttl_seconds=30)

    assert reacquired is True


async def test_the_lock_is_visible_across_independent_connections(redis_url: str) -> None:
    """A SECOND, independent Redis client (its own TCP connection) sees the lock
    that the first client acquired -- proving this genuinely coordinates across
    processes, not just within one client object's local memory (which is all
    module 05's in-memory fake could ever prove).
    """
    client_a = redis.from_url(redis_url)
    client_b = redis.from_url(redis_url)
    try:
        lock_a = RedisIdempotencyLock(client_a)
        lock_b = RedisIdempotencyLock(client_b)

        acquired_by_a = await lock_a.acquire("order-key-4", ttl_seconds=30)
        acquired_by_b = await lock_b.acquire("order-key-4", ttl_seconds=30)

        assert acquired_by_a is True
        assert acquired_by_b is False
    finally:
        await client_a.flushdb()
        await client_a.aclose()
        await client_b.aclose()
