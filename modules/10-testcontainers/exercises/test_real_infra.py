"""Exercise: real Redis, real Postgres concurrency.

Requires Docker running:
    uv run pytest modules/10-testcontainers/exercises -m exercise -v
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.docker


async def test_redis_lock_round_trip(redis_url: str) -> None:
    """TODO: create a redis.asyncio.Redis client from redis_url, wrap it in a
    RedisIdempotencyLock, and verify: acquire("k", ttl_seconds=30) returns True,
    a second acquire("k", ...) returns False, release("k") then lets a third
    acquire("k", ...) return True. Don't forget to `await client.aclose()`, and
    ideally `await client.flushdb()` first so this test doesn't depend on state left
    by another test using the same key.
    """
    raise NotImplementedError("write this test")


async def test_only_one_of_two_concurrent_requests_for_two_units_succeeds(
    engine: AsyncEngine,
) -> None:
    """TODO: seed a Product with stock_qty=2 using a real AsyncSession(engine).
    Write an inner async function that opens its OWN AsyncSession(engine), calls
    ProductRepository.reserve_stock(product_id, 2), and returns True on success /
    False if it raises InsufficientStockError (commit on success, rollback on
    failure -- see examples/test_concurrency.py for the exact shape). Run TWO of
    these concurrently with asyncio.gather and assert exactly one returns True.
    Clean up the seeded row afterward (a `finally` block, deleting by sku, works well
    -- again see examples/test_concurrency.py).
    """
    raise NotImplementedError("write this test")
