"""Consolidated test doubles for `OrderService`'s collaborators. Behaviorally
faithful, not just canned stubs (docs/02-test-doubles.md) -- see `FakeUnitOfWork`'s
docstring for the one fidelity gap that's documented rather than hidden.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from shop.domain.errors import InsufficientStockError, PaymentDeclinedError, ProductNotFoundError
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
    """Usable directly as a `uow_factory`. See
    modules/05-test-double-taxonomy/examples/conftest.py's original version of this
    class for the full explanation of its one deliberate fidelity gap: it commits
    immediately and never rolls back, so it cannot prove anything about real
    transactional atomicity (module 09-11 exist for that).
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
    def __init__(self) -> None:
        self._held: set[str] = set()

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        if key in self._held:
            return False
        self._held.add(key)
        return True

    async def release(self, key: str) -> None:
        self._held.discard(key)


class FakePaymentGateway:
    """Declines anything over `decline_above_cents` -- real (if simplified) decision
    logic, the difference between a fake and a stub (docs/02-test-doubles.md).
    """

    def __init__(self, *, decline_above_cents: int = 100_000) -> None:
        self.decline_above_cents = decline_above_cents
        self.charge_calls: list[dict[str, object]] = []
        self.refund_calls: list[dict[str, object]] = []

    async def charge(self, *, amount_cents: int, currency: str, reference: str) -> str:
        self.charge_calls.append(
            {"amount_cents": amount_cents, "currency": currency, "reference": reference}
        )
        if amount_cents > self.decline_above_cents:
            raise PaymentDeclinedError(reason="amount exceeds simulated limit")
        return f"pay_{reference}"

    async def refund(self, *, payment_reference: str, amount_cents: int) -> None:
        self.refund_calls.append(
            {"payment_reference": payment_reference, "amount_cents": amount_cents}
        )
