"""Repositories: the only place that speaks SQLAlchemy.

Everything above this layer (services, api) works with plain `domain.models` objects
and never sees a `Row` class, a `Session`, or an `IntegrityError`. That boundary is
what makes `services/orders.py` testable with an in-memory fake repository (module 05)
*and* testable against a real database (modules 09-11) without changing a line of the
service code -- only the fixture that builds the repository changes.

A note on a bug that lived here for about five minutes during this repo's own
development, because it's exactly the kind of thing module 09 exists to warn you
about: async SQLAlchemy does *not* support implicit lazy loading. `OrderRow.lines`
is a `relationship()`; touching `.lines` on a row that wasn't loaded with it eagerly
raises `sqlalchemy.exc.MissingGreenlet` -- not where you touch it, but wherever the
attribute access happens to occur, which is often deep inside `_order_to_domain`,
nowhere near the query that "caused" it. Every query below that needs `.lines` uses
`selectinload()` for exactly this reason.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shop.db.tables import OrderLineRow, OrderRow, ProductRow
from shop.domain.errors import InsufficientStockError, ProductNotFoundError
from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals, Product


def _product_to_domain(row: ProductRow) -> Product:
    return Product(
        id=row.id,
        sku=row.sku,
        name=row.name,
        unit_price_cents=row.unit_price_cents,
        stock_qty=row.stock_qty,
    )


def _order_to_domain(row: OrderRow) -> Order:
    return Order(
        id=row.id,
        customer_ref=row.customer_ref,
        status=row.status,
        lines=[
            OrderLine(
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price_cents=line.unit_price_cents,
            )
            for line in row.lines
        ],
        totals=OrderTotals(
            subtotal_cents=row.subtotal_cents,
            discount_cents=row.discount_cents,
            tax_cents=row.tax_cents,
            total_cents=row.total_cents,
        ),
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
        payment_reference=row.payment_reference,
        metadata_=dict(row.metadata_),
    )


class SupportsProductRepository(Protocol):
    """The interface `OrderService` depends on. `db.repository.ProductRepository`
    implements it against a real database; `testkit` provides an in-memory fake with
    the same shape for unit tests (module 05).
    """

    async def get(self, product_id: int) -> Product | None: ...
    async def reserve_stock(self, product_id: int, quantity: int) -> None: ...
    async def release_stock(self, product_id: int, quantity: int) -> None: ...


class SupportsOrderRepository(Protocol):
    async def add(self, order: Order) -> Order: ...
    async def get(self, order_id: int) -> Order | None: ...
    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None: ...
    async def mark_paid(self, order_id: int, *, payment_reference: str) -> None: ...
    async def mark_cancelled(self, order_id: int) -> None: ...
    async def mark_refunded(self, order_id: int) -> None: ...


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, product_id: int) -> Product | None:
        row = await self._session.get(ProductRow, product_id)
        return _product_to_domain(row) if row is not None else None

    async def add(self, product: Product) -> Product:
        row = ProductRow(
            sku=product.sku,
            name=product.name,
            unit_price_cents=product.unit_price_cents,
            stock_qty=product.stock_qty,
        )
        self._session.add(row)
        await self._session.flush()
        return _product_to_domain(row)

    async def reserve_stock(self, product_id: int, quantity: int) -> None:
        """Lock the product row, check stock, decrement it -- all in one transaction.

        `.with_for_update()` makes two concurrent callers for the last unit of stock
        queue up rather than race: the second caller's SELECT blocks until the first
        transaction commits or rolls back, so it sees the *updated* stock_qty.

        This is only true on backends that implement row locking. SQLite silently
        ignores `.with_for_update()` (verified empirically -- there's no error, no
        warning, just a plain SELECT). Module 10 makes this failure visible with a
        real concurrency test that passes against Postgres and lies to you on SQLite.
        """
        stmt = select(ProductRow).where(ProductRow.id == product_id).with_for_update()
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise ProductNotFoundError(product_id)
        if row.stock_qty < quantity:
            raise InsufficientStockError(product_id, quantity, row.stock_qty)
        row.stock_qty -= quantity

    async def release_stock(self, product_id: int, quantity: int) -> None:
        """Compensating action for a reservation that didn't end in a paid order
        (e.g. the payment gateway declined the charge). No locking needed here:
        adding stock back is always safe to interleave with other transactions.
        """
        row = await self._session.get(ProductRow, product_id)
        if row is None:
            raise ProductNotFoundError(product_id)
        row.stock_qty += quantity


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> Order:
        row = OrderRow(
            customer_ref=order.customer_ref,
            status=order.status,
            subtotal_cents=order.totals.subtotal_cents,
            discount_cents=order.totals.discount_cents,
            tax_cents=order.totals.tax_cents,
            total_cents=order.totals.total_cents,
            idempotency_key=order.idempotency_key,
            payment_reference=order.payment_reference,
            metadata_=order.metadata_,
            lines=[
                OrderLineRow(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price_cents=line.unit_price_cents,
                )
                for line in order.lines
            ],
        )
        self._session.add(row)
        await self._session.flush()
        return _order_to_domain(row)

    async def get(self, order_id: int) -> Order | None:
        row = await self._session.get(OrderRow, order_id, options=[selectinload(OrderRow.lines)])
        return _order_to_domain(row) if row is not None else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        stmt = (
            select(OrderRow)
            .where(OrderRow.idempotency_key == idempotency_key)
            .options(selectinload(OrderRow.lines))
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _order_to_domain(row) if row is not None else None

    async def mark_paid(self, order_id: int, *, payment_reference: str) -> None:
        row = await self._session.get(OrderRow, order_id)
        if row is None:
            raise LookupError(f"order {order_id} not found")
        row.status = OrderStatus.PAID
        row.payment_reference = payment_reference

    async def mark_cancelled(self, order_id: int) -> None:
        row = await self._session.get(OrderRow, order_id)
        if row is None:
            raise LookupError(f"order {order_id} not found")
        row.status = OrderStatus.CANCELLED

    async def mark_refunded(self, order_id: int) -> None:
        row = await self._session.get(OrderRow, order_id)
        if row is None:
            raise LookupError(f"order {order_id} not found")
        row.status = OrderStatus.REFUNDED
