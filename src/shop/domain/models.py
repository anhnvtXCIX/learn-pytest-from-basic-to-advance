"""Plain-Python domain objects.

These are *not* SQLAlchemy models. Keeping them as plain dataclasses means
`domain/pricing.py` and the rest of the business logic can be unit-tested with zero
database, zero event loop, zero I/O -- just objects in, objects out. The `db` layer's
repositories are responsible for translating to/from the ORM's mapped classes
(see db/repository.py). This is the "domain model / ORM model" split described in
Percival & Gregory, *Architecture Patterns with Python*, ch. 2-4 (free at
https://www.cosmicpython.com/book/chapter_02_repository.html).

All money is represented in integer cents to avoid float rounding bugs -- see
pricing.py for why this matters for testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass(frozen=True, slots=True)
class Product:
    id: int
    sku: str
    name: str
    unit_price_cents: int
    stock_qty: int


@dataclass(frozen=True, slots=True)
class RequestedLine:
    """What a caller asks for: a product and a quantity. Deliberately has no price --
    `OrderService.place_order` resolves the current price itself, inside the same
    transaction that reserves stock. Trusting a client-supplied price would let
    anyone order a $500 item for a penny; this is a real bug class, not a hypothetical.
    """

    product_id: int
    quantity: int


@dataclass(frozen=True, slots=True)
class OrderLine:
    product_id: int
    quantity: int
    unit_price_cents: int  # snapshotted at order time, independent of later price changes

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity


@dataclass(frozen=True, slots=True)
class OrderTotals:
    subtotal_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int


@dataclass(slots=True)
class Order:
    id: int | None
    customer_ref: str
    status: OrderStatus
    lines: list[OrderLine]
    totals: OrderTotals
    idempotency_key: str
    created_at: datetime
    payment_reference: str | None = None
    metadata_: dict[str, str] = field(default_factory=dict)
