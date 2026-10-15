"""Exercise: real Redis, real Postgres concurrency.

Requires Docker running:
    uv run pytest modules/10-testcontainers/exercises -m exercise -v
"""

from __future__ import annotations

import asyncio

import pytest
import redis.asyncio as redis
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from shop.db.repository import ProductRepository
from shop.db.tables import ProductRow
from shop.domain.errors import InsufficientStockError
from shop.domain.models import Product
from shop.gateways.cache import RedisIdempotencyLock

pytestmark = pytest.mark.docker


async def test_redis_lock_round_trip(redis_url: str) -> None:
    """TODO: create a redis.asyncio.Redis client from redis_url, wrap it in a
    RedisIdempotencyLock, and verify: acquire("k", ttl_seconds=30) returns True,
    a second acquire("k", ...) returns False, release("k") then lets a third
    acquire("k", ...) return True. Don't forget to `await client.aclose()`, and
    ideally `await client.flushdb()` first so this test doesn't depend on state left
    by another test using the same key.
    """
    client = redis.from_url(redis_url)
    lock = RedisIdempotencyLock(client)

    acquired_first = await lock.acquire("k", ttl_seconds=30)
    acquired_second = await lock.acquire("k", ttl_seconds=30)

    assert acquired_first is True
    assert acquired_second is False

    await client.flushdb()
    await client.aclose()


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
    async with AsyncSession(engine) as session:
        repo = ProductRepository(session)
        product = await repo.add(
            Product(id=1, sku="NOPE", name="Nope", unit_price_cents=1_000, stock_qty=2)
        )

        await session.commit()
        product_id = product.id

    async def try_reserve() -> bool:
        async with AsyncSession(engine) as session:
            repo = ProductRepository(session)

            try:
                await repo.reserve_stock(product_id, 2)
            except InsufficientStockError:
                await session.rollback()
                return False
            else:
                await session.commit()
                return True

    try:
        results = await asyncio.gather(try_reserve(), try_reserve())

        assert sorted(results) == [False, True], (
            "exactly one reservation should succeed for a single unit of stock"
        )
    finally:
        async with AsyncSession(engine) as session:
            await session.execute(delete(ProductRow).where(ProductRow.sku == "NOPE"))
            await session.commit()
