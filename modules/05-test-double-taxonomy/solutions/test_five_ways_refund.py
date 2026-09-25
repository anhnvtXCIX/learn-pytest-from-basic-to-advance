"""Reference solution for exercises/test_five_ways_refund.py."""

from __future__ import annotations

from datetime import datetime

import pytest

from shop.domain.errors import InvalidOrderStateError
from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals, Product
from shop.services.orders import OrderService

pytestmark = pytest.mark.unit


def seed_paid_order(fake_uow) -> Order:
    fake_uow.seed_product(
        Product(id=1, sku="WIDGET", name="Widget", unit_price_cents=1_500, stock_qty=3)
    )
    order = Order(
        id=1,
        customer_ref="cust-1",
        status=OrderStatus.PAID,
        lines=[OrderLine(product_id=1, quantity=2, unit_price_cents=1_500)],
        totals=OrderTotals(subtotal_cents=3_000, discount_cents=0, tax_cents=0, total_cents=3_000),
        idempotency_key="key-1",
        created_at=datetime(2026, 1, 1),
        payment_reference="pay_existing_ref",
    )
    fake_uow.orders._orders[order.id] = order
    return order


def seed_pending_order(fake_uow) -> Order:
    fake_uow.seed_product(
        Product(id=1, sku="WIDGET", name="Widget", unit_price_cents=1_500, stock_qty=3)
    )
    order = Order(
        id=1,
        customer_ref="cust-1",
        status=OrderStatus.PENDING,
        lines=[OrderLine(product_id=1, quantity=2, unit_price_cents=1_500)],
        totals=OrderTotals(subtotal_cents=3_000, discount_cents=0, tax_cents=0, total_cents=3_000),
        idempotency_key="key-1",
        created_at=datetime(2026, 1, 1),
        payment_reference=None,
    )
    fake_uow.orders._orders[order.id] = order
    return order


def make_service(payment_gateway, fake_uow, fake_clock, fake_lock) -> OrderService:
    return OrderService(
        uow_factory=fake_uow,
        payment_gateway=payment_gateway,
        idempotency_lock=fake_lock,
        clock=fake_clock,
        tax_rate=0.0,
    )


class DummyPaymentGateway:
    async def charge(self, **kwargs):
        raise AssertionError("charge() should never be called from cancel_order")

    async def refund(self, **kwargs):
        raise AssertionError("refund() should never be called: order isn't PAID")


async def test_dummy_proves_refund_is_never_attempted_on_a_pending_order(
    fake_uow, fake_clock, fake_lock
) -> None:
    seed_pending_order(fake_uow)
    service = make_service(DummyPaymentGateway(), fake_uow, fake_clock, fake_lock)

    with pytest.raises(InvalidOrderStateError):
        await service.cancel_order(1)


class StubPaymentGateway:
    async def refund(self, **kwargs) -> None:
        pass

    async def charge(self, **kwargs):
        raise AssertionError("not used in this test")


async def test_stub_lets_cancel_reach_refunded_status(fake_uow, fake_clock, fake_lock) -> None:
    seed_paid_order(fake_uow)
    service = make_service(StubPaymentGateway(), fake_uow, fake_clock, fake_lock)

    order = await service.cancel_order(1)

    assert order.status == OrderStatus.REFUNDED


class SpyPaymentGateway(StubPaymentGateway):
    def __init__(self) -> None:
        self.refund_calls: list[dict] = []

    async def refund(self, **kwargs) -> None:
        self.refund_calls.append(kwargs)
        await super().refund(**kwargs)


async def test_spy_proves_the_correct_refund_amount_and_reference(
    fake_uow, fake_clock, fake_lock
) -> None:
    seed_paid_order(fake_uow)
    gateway = SpyPaymentGateway()
    service = make_service(gateway, fake_uow, fake_clock, fake_lock)

    await service.cancel_order(1)

    assert len(gateway.refund_calls) == 1
    assert gateway.refund_calls[0]["payment_reference"] == "pay_existing_ref"
    assert gateway.refund_calls[0]["amount_cents"] == 3_000
