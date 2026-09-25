"""Same UNIQUE constraint, same abstract SQLAlchemy exception class
(`IntegrityError`) on both engines -- but the underlying driver exception wrapped
inside it is genuinely different, which matters the moment code tries to inspect
*why* an IntegrityError happened (e.g. distinguishing a unique violation from a
foreign key violation) rather than just catching the base class.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from shop.db.uow import UnitOfWork
from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals, Product

pytestmark = pytest.mark.docker


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


async def test_duplicate_idempotency_key_is_an_integrity_error_here_too(sessionmaker) -> None:
    async with UnitOfWork(sessionmaker) as uow:
        product = await uow.products.add(
            Product(id=0, sku="PG-DUP-KEY", name="W", unit_price_cents=100, stock_qty=10)
        )
        await uow.commit()

    async with UnitOfWork(sessionmaker) as uow:
        await uow.orders.add(_make_order(product.id, "pg-dup-key"))
        await uow.commit()

    # Note the shape here: `pytest.raises` wraps the WHOLE `async with UnitOfWork`
    # block, not just the inner `.add()` call. This isn't stylistic -- it's required
    # on Postgres specifically. Once a statement inside a Postgres transaction
    # fails, the ENTIRE transaction is aborted ("current transaction is aborted,
    # commands ignored until end of transaction block") until something rolls it
    # back; `UnitOfWork.__aexit__` only calls `session.rollback()` when it SEES an
    # exception propagate out of the `async with` block. Catching the IntegrityError
    # *inside* the block (the way module 09's SQLite version of this same test does)
    # hides it from `__aexit__`, leaves the aborted transaction unrolled-back, and
    # breaks the NEXT thing that touches this session -- confirmed by hitting
    # exactly that failure while writing this test. SQLite has no equivalent
    # "poisoned transaction" state, which is exactly why module 09's version gets
    # away with the pattern this one can't.
    with pytest.raises(IntegrityError) as excinfo:
        async with UnitOfWork(sessionmaker) as second_uow:
            await second_uow.orders.add(_make_order(product.id, "pg-dup-key"))

    # SQLAlchemy's IntegrityError wraps a DRIVER-SPECIFIC exception underneath, in
    # `.orig`. Checked empirically (not assumed) against both engines while writing
    # this test:
    #   - Postgres/asyncpg: `.orig` is (SQLAlchemy's adapter around) asyncpg's
    #     `UniqueViolationError` -- a SPECIFIC subtype naming exactly which kind of
    #     constraint failed. A foreign-key violation would give a different type
    #     name (`ForeignKeyViolationError`).
    #   - SQLite/aiosqlite (module 09): `.orig` is plain `sqlite3.IntegrityError` --
    #     ONE generic type for every kind of constraint violation, unique or
    #     foreign-key or check, all alike.
    # Code that wants to distinguish "which constraint failed" rather than just
    # "some constraint failed" can do it precisely on Postgres and cannot on SQLite.
    assert type(excinfo.value.orig).__name__ == "UniqueViolationError"
