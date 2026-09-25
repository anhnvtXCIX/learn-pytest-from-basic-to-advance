"""Reference solution for exercises/test_real_infra.py."""

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
    client = redis.from_url(redis_url)
    await client.flushdb()
    lock = RedisIdempotencyLock(client)

    try:
        assert await lock.acquire("exercise-key", ttl_seconds=30) is True
        assert await lock.acquire("exercise-key", ttl_seconds=30) is False

        await lock.release("exercise-key")

        assert await lock.acquire("exercise-key", ttl_seconds=30) is True
    finally:
        await client.flushdb()
        await client.aclose()


async def test_only_one_of_two_concurrent_requests_for_two_units_succeeds(
    engine: AsyncEngine,
) -> None:
    async with AsyncSession(engine) as session:
        repo = ProductRepository(session)
        product = await repo.add(
            Product(id=0, sku="EXERCISE-RACE", name="X", unit_price_cents=100, stock_qty=2)
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
        assert sorted(results) == [False, True]
    finally:
        async with AsyncSession(engine) as session:
            await session.execute(delete(ProductRow).where(ProductRow.sku == "EXERCISE-RACE"))
            await session.commit()
