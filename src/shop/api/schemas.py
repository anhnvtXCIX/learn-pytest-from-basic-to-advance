"""Request/response models -- the HTTP contract, kept separate from `domain.models`.

This separation is what module 11 leans on: a full API test asserts against this
contract (JSON field names, HTTP status codes) without caring how `OrderService`
represents an order internally.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from shop.domain.models import Order, OrderStatus


class RequestedLineIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    customer_ref: str
    lines: list[RequestedLineIn] = Field(min_length=1)
    idempotency_key: str


class OrderLineOut(BaseModel):
    product_id: int
    quantity: int
    unit_price_cents: int


class OrderOut(BaseModel):
    id: int
    customer_ref: str
    status: OrderStatus
    lines: list[OrderLineOut]
    subtotal_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int
    payment_reference: str | None
    created_at: datetime

    @classmethod
    def from_domain(cls, order: Order) -> OrderOut:
        assert order.id is not None
        return cls(
            id=order.id,
            customer_ref=order.customer_ref,
            status=order.status,
            lines=[
                OrderLineOut(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price_cents=line.unit_price_cents,
                )
                for line in order.lines
            ],
            subtotal_cents=order.totals.subtotal_cents,
            discount_cents=order.totals.discount_cents,
            tax_cents=order.totals.tax_cents,
            total_cents=order.totals.total_cents,
            payment_reference=order.payment_reference,
            created_at=order.created_at,
        )


class ErrorOut(BaseModel):
    detail: str
