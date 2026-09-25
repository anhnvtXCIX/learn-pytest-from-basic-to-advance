"""The payoff of this whole tier: a genuine race condition, provably prevented by
`.with_for_update()` -- against real Postgres, with two REAL, independent database
connections. This cannot be tested honestly against SQLite (module 09 already
proved `.with_for_update()` compiles to a no-op there).

This test deliberately does NOT use the `sessionmaker` fixture (module 09/10's
rollback-per-test pattern) -- that pattern binds every session to ONE shared
connection, which would make two "concurrent" reservations trivially serialize
through Python's own asyncio scheduling rather than through Postgres's row locking.
A real concurrency test needs two independent connections, each doing a REAL commit,
so this test manages (and cleans up) its own data instead.
"""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from shop.db.repository import ProductRepository
from shop.db.tables import ProductRow
from shop.domain.errors import InsufficientStockError
from shop.domain.models import Product

pytestmark = pytest.mark.docker


async def test_concurrent_reservations_for_the_last_unit_are_serialized_not_racy(
    engine: AsyncEngine,
) -> None:
    async with AsyncSession(engine) as session:
        repo = ProductRepository(session)
        product = await repo.add(
            Product(id=0, sku="RACE-TEST", name="Last Unit", unit_price_cents=100, stock_qty=1)
        )
        await session.commit()
        product_id = product.id

    async def try_reserve() -> bool:
        async with AsyncSession(engine) as session:
            repo = ProductRepository(session)
            try:
                await repo.reserve_stock(product_id, 1)
            except InsufficientStockError:
                await session.rollback()
                return False
            else:
                await session.commit()
                return True

    try:
        # Two REAL, concurrent attempts to reserve the one remaining unit. Without
        # `.with_for_update()` actually locking the row on Postgres, both could read
        # stock_qty=1 before either writes, and both would "succeed" -- selling the
        # same unit twice. With it, the second transaction's SELECT blocks until the
        # first commits or rolls back, and sees the updated (now zero) stock.
        results = await asyncio.gather(try_reserve(), try_reserve())

        assert sorted(results) == [False, True], (
            "exactly one reservation should succeed for a single unit of stock"
        )
    finally:
        async with AsyncSession(engine) as session:
            await session.execute(delete(ProductRow).where(ProductRow.sku == "RACE-TEST"))
            await session.commit()
