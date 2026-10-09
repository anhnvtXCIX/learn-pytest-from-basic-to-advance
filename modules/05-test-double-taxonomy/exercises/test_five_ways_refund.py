"""Exercise: write three test doubles yourself (dummy, stub, spy) against
`OrderService.cancel_order`'s refund path -- the same taxonomy as
examples/test_five_ways.py, applied to a different method.

    make ex M=05
"""

from __future__ import annotations

from datetime import datetime

import pytest

from shop.domain.errors import InvalidOrderStateError
from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals, Product
from shop.services.orders import OrderService

pytestmark = pytest.mark.unit


def seed_paid_order(fake_uow) -> Order:
    """Puts a PAID $30 order (2 units of product 1 at $15) directly into the fake
    UoW's storage, bypassing place_order -- this exercise is about cancel_order, so
    we don't need to re-run the whole placement flow to get there.
    """
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
    # Reaching into the fake's storage directly (instead of going through
    # `fake_uow.orders.add`, which would assign its own id) -- fine for a test
    # double you control, exactly the kind of thing you'd never do to a real
    # repository/session.
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
    """TODO: seed_paid_order gives you a PAID order -- instead, build (or mutate) an
    order with status=PENDING using the same shape, put it in fake_uow, and assert
    that calling cancel_order on it raises InvalidOrderStateError WITHOUT ever
    calling DummyPaymentGateway.refund (the dummy raises if it's called, so a plain
    pytest.raises(InvalidOrderStateError) around the call is enough to prove it).
    """
    order = Order(
        id=1,
        customer_ref="cust-1",
        status=OrderStatus.PENDING,
        lines=[OrderLine(product_id=1, quantity=2, unit_price_cents=1_500)],
        totals=OrderTotals(subtotal_cents=3_000, discount_cents=0, tax_cents=0, total_cents=3_000),
        idempotency_key="key-1",
        created_at=datetime(2026, 1, 1),
        payment_reference="pay_existing_ref",
    )
    fake_uow.orders._orders[order.id] = order

    service = make_service(DummyPaymentGateway(), fake_uow, fake_clock, fake_lock)
    with pytest.raises(InvalidOrderStateError):
        await service.cancel_order(order_id=1)


class StubPaymentGateway:
    async def refund(self, **kwargs) -> None:
        pass

    async def charge(self, **kwargs):
        raise AssertionError("not used in this test")


async def test_stub_lets_cancel_reach_refunded_status(fake_uow, fake_clock, fake_lock) -> None:
    # TODO: seed_paid_order(fake_uow), build a service with StubPaymentGateway, call
    # cancel_order(1), and assert the returned order's status is OrderStatus.REFUNDED.
    seed_paid_order(fake_uow)
    stub_gateway = StubPaymentGateway()

    service = make_service(stub_gateway, fake_uow, fake_clock, fake_lock)

    canceled_order = await service.cancel_order(1)

    assert canceled_order.status == OrderStatus.REFUNDED
    assert fake_uow.products._products[1].stock_qty == 5, "product stock was not released"


class SpyPaymentGateway(StubPaymentGateway):
    def __init__(self) -> None:
        self.refund_calls: list[dict] = []

    async def refund(self, **kwargs) -> None:
        # TODO: record kwargs into self.refund_calls, then call the stub behavior.
        self.refund_calls.append(kwargs)


async def test_spy_proves_the_correct_refund_amount_and_reference(
    fake_uow, fake_clock, fake_lock
) -> None:
    # TODO: seed_paid_order(fake_uow), use SpyPaymentGateway, call cancel_order(1),
    # then assert gateway.refund_calls has exactly one call with
    # payment_reference="pay_existing_ref" and amount_cents=3_000.
    seed_paid_order(fake_uow)
    spy_gateway = SpyPaymentGateway()

    service = make_service(spy_gateway, fake_uow, fake_clock, fake_lock)

    refunded_order = await service.cancel_order(1)

    assert refunded_order.status == OrderStatus.REFUNDED
    assert len(spy_gateway.refund_calls) == 1
    assert spy_gateway.refund_calls[0]["payment_reference"] == "pay_existing_ref"
    assert spy_gateway.refund_calls[0]["amount_cents"] == 3_000
