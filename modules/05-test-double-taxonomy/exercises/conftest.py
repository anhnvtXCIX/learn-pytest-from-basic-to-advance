"""A hand-rolled in-memory Unit of Work, Clock, and idempotency lock -- the generic
harness modules 05-08 all use to exercise `OrderService` with every real I/O
collaborator replaced. Each of those modules' PaymentGateway double is different
(that's the actual lesson); this plumbing is the same everywhere, which is exactly
why module 13 eventually extracts it into `testkit` -- for now, per this repo's
convention, it's duplicated locally per module (see CLAUDE.md).

A DELIBERATE FIDELITY GAP, worth understanding rather than hiding: this fake commits
immediately and never rolls back. `OrderService.place_order` reserves stock for
several lines inside one `async with uow_factory() as uow:` block; if line 3 of 3
raised partway through (say, a bad product id), the REAL `UnitOfWork` would roll back
lines 1-2's reservations along with it (SQLAlchemy session rollback), but THIS fake
would leave them reserved, because it has no concept of an uncommitted transaction.
That's not a bug to fix here -- it's the concrete reason `docs/05-backend-testing-playbook.md`
insists a fake, however careful, can't replace a real integration test for anything
that depends on transactional behavior. Module 09 tests exactly this gap against a
real database.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import pytest

from shop.domain.errors import InsufficientStockError, ProductNotFoundError
from shop.domain.models import Order, OrderStatus, Product


class InMemoryProductRepository:
    def __init__(self, products: dict[int, Product]) -> None:
        self._products = products

    async def get(self, product_id: int) -> Product | None:
        return self._products.get(product_id)

    async def reserve_stock(self, product_id: int, quantity: int) -> None:
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        if product.stock_qty < quantity:
            raise InsufficientStockError(product_id, quantity, product.stock_qty)
        self._products[product_id] = replace(product, stock_qty=product.stock_qty - quantity)

    async def release_stock(self, product_id: int, quantity: int) -> None:
        product = self._products[product_id]
        self._products[product_id] = replace(product, stock_qty=product.stock_qty + quantity)


class InMemoryOrderRepository:
    def __init__(self, orders: dict[int, Order]) -> None:
        self._orders = orders

    async def add(self, order: Order) -> Order:
        new_id = max(self._orders.keys(), default=0) + 1
        order.id = new_id
        self._orders[new_id] = order
        return order

    async def get(self, order_id: int) -> Order | None:
        return self._orders.get(order_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        return next(
            (o for o in self._orders.values() if o.idempotency_key == idempotency_key), None
        )

    async def mark_paid(self, order_id: int, *, payment_reference: str) -> None:
        order = self._orders[order_id]
        order.status = OrderStatus.PAID
        order.payment_reference = payment_reference

    async def mark_cancelled(self, order_id: int) -> None:
        self._orders[order_id].status = OrderStatus.CANCELLED

    async def mark_refunded(self, order_id: int) -> None:
        self._orders[order_id].status = OrderStatus.REFUNDED


class FakeUnitOfWork:
    """Usable directly as a `uow_factory`: `OrderService(uow_factory=FakeUnitOfWork(), ...)`.
    Calling it returns itself, so every `async with uow_factory() as uow:` in
    `OrderService` shares the same underlying dicts -- that's what makes state
    persist "across transactions" the way a real database would, within the limits
    described in this file's module docstring.
    """

    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._orders: dict[int, Order] = {}
        self.products = InMemoryProductRepository(self._products)
        self.orders = InMemoryOrderRepository(self._orders)

    def __call__(self) -> FakeUnitOfWork:
        return self

    async def __aenter__(self) -> FakeUnitOfWork:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def commit(self) -> None:
        pass

    def seed_product(self, product: Product) -> Product:
        self._products[product.id] = product
        return product


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakeIdempotencyLock:
    """Real semantics (first caller for a key wins, until released), zero Redis."""

    def __init__(self) -> None:
        self._held: set[str] = set()

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        if key in self._held:
            return False
        self._held.add(key)
        return True

    async def release(self, key: str) -> None:
        self._held.discard(key)


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock(datetime(2026, 1, 1))


@pytest.fixture
def fake_lock() -> FakeIdempotencyLock:
    return FakeIdempotencyLock()
