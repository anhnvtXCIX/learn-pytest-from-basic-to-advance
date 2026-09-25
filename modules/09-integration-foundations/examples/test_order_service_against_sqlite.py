"""`OrderService` against a REAL `UnitOfWork` and real SQLite -- this is what
"integration test" means for the service layer (docs/05-backend-testing-playbook.md):
real database, fake payment gateway and lock (still not worth making real for this
tier -- that's module 11's job once the API layer is involved too).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shop.db.uow import UnitOfWork
from shop.domain.errors import InsufficientStockError
from shop.domain.models import Product, RequestedLine
from shop.services.orders import OrderService

# No loop-scope marker needed here -- conftest.py's `engine` fixture already
# declares `loop_scope="module"` on itself, which is sufficient on its own. See
# test_rollback_isolation.py's comment for how that was confirmed.


class FakeClock:
    def now(self):
        return datetime(2026, 1, 1, tzinfo=UTC)


class FakePaymentGateway:
    async def charge(self, **kwargs) -> str:
        return "pay_ref"

    async def refund(self, **kwargs) -> None:
        pass


class FakeLock:
    def __init__(self) -> None:
        self._held: set[str] = set()

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        if key in self._held:
            return False
        self._held.add(key)
        return True

    async def release(self, key: str) -> None:
        self._held.discard(key)


def make_service(sessionmaker) -> OrderService:
    return OrderService(
        uow_factory=lambda: UnitOfWork(sessionmaker),
        payment_gateway=FakePaymentGateway(),
        idempotency_lock=FakeLock(),
        clock=FakeClock(),
        tax_rate=0.0,
    )


async def test_place_order_persists_to_a_real_database(sessionmaker) -> None:
    async with UnitOfWork(sessionmaker) as uow:
        product = await uow.products.add(
            Product(id=0, sku="REAL-DB-WIDGET", name="Widget", unit_price_cents=1_000, stock_qty=5)
        )
        await uow.commit()

    service = make_service(sessionmaker)
    order = await service.place_order(
        customer_ref="cust-1",
        requested_lines=[RequestedLine(product_id=product.id, quantity=2)],
        idempotency_key="key-1",
    )

    # Fetch it back through a COMPLETELY SEPARATE unit of work/session, proving it
    # was actually committed to the database, not just held in the object we got back.
    async with UnitOfWork(sessionmaker) as uow:
        reloaded = await uow.orders.get(order.id)

    assert reloaded is not None
    assert reloaded.status.value == "paid"
    assert reloaded.totals.total_cents == 2_000


async def test_a_failed_second_line_rolls_back_the_first_lines_reservation_too(
    sessionmaker,
) -> None:
    """The case module 05's FakeUnitOfWork explicitly CANNOT prove (see its module
    docstring): line 1 succeeds and decrements real stock, line 2 fails, and the
    whole transaction -- including line 1's already-applied decrement -- rolls back
    together, because both reservations happened inside one real database
    transaction. This is the concrete payoff of testing against a real engine.
    """
    async with UnitOfWork(sessionmaker) as uow:
        plenty = await uow.products.add(
            Product(id=0, sku="PLENTY-OF-STOCK", name="A", unit_price_cents=1_000, stock_qty=10)
        )
        scarce = await uow.products.add(
            Product(id=0, sku="ALMOST-OUT-OF-STOCK", name="B", unit_price_cents=1_000, stock_qty=1)
        )
        await uow.commit()

    service = make_service(sessionmaker)

    with pytest.raises(InsufficientStockError):
        await service.place_order(
            customer_ref="cust-1",
            requested_lines=[
                RequestedLine(product_id=plenty.id, quantity=2),  # would succeed alone
                RequestedLine(product_id=scarce.id, quantity=5),  # fails: only 1 in stock
            ],
            idempotency_key="key-2",
        )

    async with UnitOfWork(sessionmaker) as uow:
        reloaded_plenty = await uow.products.get(plenty.id)
        reloaded_scarce = await uow.products.get(scarce.id)
        order = await uow.orders.get_by_idempotency_key("key-2")

    assert reloaded_plenty.stock_qty == 10  # NOT left at 8 -- the whole tx rolled back
    assert reloaded_scarce.stock_qty == 1
    assert order is None  # no partial order was left behind
