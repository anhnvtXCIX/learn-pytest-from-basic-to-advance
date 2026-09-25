"""Exercise: fix conftest.py's `engine` fixture first (see its module docstring),
then complete the two tests below.

    make ex M=09
"""

from __future__ import annotations

from datetime import UTC, datetime

from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals


async def test_rollback_isolates_this_test_from_the_next_one(sessionmaker) -> None:
    """TODO: using `sessionmaker() as session` and `ProductRepository`, add a Product
    with sku="EXERCISE-SHARED-SKU" and commit. The next test does the exact same
    thing with the same sku -- if this doesn't roll back cleanly, that test will fail
    with a UNIQUE constraint error.
    """
    raise NotImplementedError("write this test")


async def test_rollback_isolates_this_test_from_the_previous_one(sessionmaker) -> None:
    # TODO: same as above -- same sku, same pattern. If it passes, rollback worked.
    raise NotImplementedError("write this test")


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
    """TODO: seed a Product via UnitOfWork, add() an order with idempotency_key
    "dup-key" and commit, then in a SECOND UnitOfWork try to add() another order with
    the SAME idempotency_key and assert it raises sqlalchemy.exc.IntegrityError.
    (Check examples/test_sqlite_limitations.py if you get stuck on where exactly the
    error surfaces.)
    """
    raise NotImplementedError("write this test")
