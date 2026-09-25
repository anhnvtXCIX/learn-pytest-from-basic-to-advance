"""Reference solution for exercises/test_foundations.py."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from shop.db.repository import ProductRepository
from shop.db.uow import UnitOfWork
from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals, Product


async def test_rollback_isolates_this_test_from_the_next_one(sessionmaker) -> None:
    async with sessionmaker() as session:
        repo = ProductRepository(session)
        await repo.add(
            Product(id=0, sku="EXERCISE-SHARED-SKU", name="A", unit_price_cents=100, stock_qty=1)
        )
        await session.commit()


async def test_rollback_isolates_this_test_from_the_previous_one(sessionmaker) -> None:
    async with sessionmaker() as session:
        repo = ProductRepository(session)
        await repo.add(
            Product(id=0, sku="EXERCISE-SHARED-SKU", name="B", unit_price_cents=200, stock_qty=1)
        )
        await session.commit()


def _make_order(product_id: int, idempotency_key: str) -> Order:
    return Order(
        id=None,
        customer_ref="cust-1",
        status=OrderStatus.PENDING,
        lines=[OrderLine(product_id=product_id, quantity=1, unit_price_cents=500)],
        totals=OrderTotals(subtotal_cents=500, discount_cents=0, tax_cents=0, total_cents=500),
        idempotency_key=idempotency_key,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def test_duplicate_idempotency_key_is_rejected_by_the_database(sessionmaker) -> None:
    async with UnitOfWork(sessionmaker) as uow:
        product = await uow.products.add(
            Product(id=0, sku="EXERCISE-DUP-KEY", name="W", unit_price_cents=500, stock_qty=10)
        )
        await uow.commit()

    async with UnitOfWork(sessionmaker) as uow:
        await uow.orders.add(_make_order(product.id, "dup-key"))
        await uow.commit()

    async with UnitOfWork(sessionmaker) as second_uow:
        with pytest.raises(IntegrityError):
            await second_uow.orders.add(_make_order(product.id, "dup-key"))
