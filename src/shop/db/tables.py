"""SQLAlchemy ORM mappings.

These are intentionally named `*Row` and kept separate from the plain `domain.models`
classes (module 09's README explains why). Note two places designed to behave
differently on SQLite vs Postgres -- both are load-bearing for module 10:

1. `metadata_` uses `JSON().with_variant(JSONB, "postgresql")`: real JSONB (with
   indexing, containment operators, etc.) in Postgres, a plain text column that
   happens to hold JSON everywhere else.
2. `idempotency_key` has a UNIQUE constraint. SQLite and Postgres both enforce it,
   but they report the violation as different exception types, which is exactly
   the kind of thing that "test only against SQLite" hides until production.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shop.db.base import Base
from shop.domain.models import OrderStatus


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    unit_price_cents: Mapped[int]
    stock_qty: Mapped[int]


class OrderRow(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_ref: Mapped[str]
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.PENDING)
    subtotal_cents: Mapped[int]
    discount_cents: Mapped[int]
    tax_cents: Mapped[int]
    total_cents: Mapped[int]
    idempotency_key: Mapped[str] = mapped_column(unique=True)
    payment_reference: Mapped[str | None] = mapped_column(default=None)
    metadata_: Mapped[dict[str, str]] = mapped_column(
        "metadata", JSON().with_variant(JSONB, "postgresql"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    lines: Mapped[list[OrderLineRow]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderLineRow(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    unit_price_cents: Mapped[int]

    order: Mapped[OrderRow] = relationship(back_populates="lines")
