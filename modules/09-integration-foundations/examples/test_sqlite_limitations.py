"""What SQLite honestly CAN'T tell you -- setting up module 10's motivation for a
real Postgres tier. Both findings here were verified empirically while building this
repo (see src/shop/db/repository.py's docstring), not assumed from documentation.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from shop.db.tables import ProductRow
from shop.db.uow import UnitOfWork
from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals, Product


async def test_with_for_update_compiles_to_a_plain_select_on_sqlite(sessionmaker) -> None:
    """`ProductRepository.reserve_stock` uses `.with_for_update()` specifically to
    make concurrent reservations for the same row safe (module 10 proves this
    against real Postgres). On SQLite, the clause is silently dropped -- no error,
    no warning, just a plain SELECT. This test proves the SQL SQLAlchemy actually
    generates has no locking clause in it; it does NOT (and cannot) prove anything
    about concurrent safety, because SQLite doesn't have real row-level locking to
    demonstrate the absence of.
    """
    async with sessionmaker() as session:
        stmt = select(ProductRow).where(ProductRow.id == 1).with_for_update()
        compiled = str(stmt.compile(session.bind, compile_kwargs={"literal_binds": True}))

    assert "FOR UPDATE" not in compiled.upper()


def _make_order(product_id: int, idempotency_key: str) -> Order:
    return Order(
        id=None,
        customer_ref="cust-1",
        status=OrderStatus.PENDING,
        lines=[OrderLine(product_id=product_id, quantity=1, unit_price_cents=100)],
        totals=OrderTotals(subtotal_cents=100, discount_cents=0, tax_cents=0, total_cents=100),
        idempotency_key=idempotency_key,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def test_duplicate_idempotency_key_raises_integrity_error(sessionmaker) -> None:
    """OrderRow.idempotency_key is UNIQUE. SQLite enforces it (so does Postgres --
    module 10 shows the same test passing there too), but this only proves the
    constraint fires -- there is currently no translation layer catching this
    IntegrityError anywhere above the repository (a real gap; see this module's
    exercise for closing it).
    """
    async with UnitOfWork(sessionmaker) as uow:
        product = await uow.products.add(
            Product(id=0, sku="DUPLICATE-KEY-TEST", name="W", unit_price_cents=100, stock_qty=10)
        )
        await uow.commit()

    async with UnitOfWork(sessionmaker) as uow:
        await uow.orders.add(_make_order(product.id, "same-key-both-times"))
        await uow.commit()

    async with UnitOfWork(sessionmaker) as second_uow:
        # The repository's `add()` flushes immediately (to get the new row's
        # generated id back) -- so the constraint violation surfaces here, at
        # `add()`, not at the later `commit()` you might expect it at.
        with pytest.raises(IntegrityError):
            await second_uow.orders.add(_make_order(product.id, "same-key-both-times"))
