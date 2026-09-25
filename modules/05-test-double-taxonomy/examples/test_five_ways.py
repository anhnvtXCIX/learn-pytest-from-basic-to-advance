"""The same collaborator (`PaymentGateway`), doubled five different ways, each
proving a different kind of thing about `OrderService.place_order`. Read
docs/02-test-doubles.md first if you haven't -- this file is that taxonomy made
concrete.

The scenario throughout: a $30 order (2 units at $15) for product id 1, with 5 in
stock.
"""

from __future__ import annotations

import pytest

from shop.domain.errors import InsufficientStockError, PaymentDeclinedError
from shop.domain.models import Product, RequestedLine
from shop.services.orders import OrderService

pytestmark = pytest.mark.unit


def make_service(payment_gateway, fake_uow, fake_clock, fake_lock) -> OrderService:
    fake_uow.seed_product(
        Product(id=1, sku="WIDGET", name="Widget", unit_price_cents=1_500, stock_qty=5)
    )
    return OrderService(
        uow_factory=fake_uow,
        payment_gateway=payment_gateway,
        idempotency_lock=fake_lock,
        clock=fake_clock,
        tax_rate=0.0,  # zero tax keeps the arithmetic in each test trivial
    )


# --- 1. Dummy: never actually called, and the test proves it ----------------------


class DummyPaymentGateway:
    """A dummy exists to satisfy a required parameter when the test path shouldn't
    reach it at all. Both methods raise if called -- if this test is wrong about
    the code path, it fails loudly instead of quietly using a fake charge.
    """

    async def charge(self, **kwargs):
        raise AssertionError("charge() should never be called: stock check must fail first")

    async def refund(self, **kwargs):
        raise AssertionError("refund() should never be called in this test")


async def test_dummy_proves_payment_is_never_attempted_when_stock_is_insufficient(
    fake_uow, fake_clock, fake_lock
) -> None:
    service = make_service(DummyPaymentGateway(), fake_uow, fake_clock, fake_lock)

    with pytest.raises(InsufficientStockError):
        await service.place_order(
            customer_ref="cust-1",
            requested_lines=[RequestedLine(product_id=1, quantity=100)],  # more than in stock
            idempotency_key="key-1",
        )
    # No assertion needed beyond the raise: if `charge` HAD been called, the dummy
    # itself would have raised AssertionError from inside place_order, failing this
    # test with a different, very clear error.


# --- 2. Stub: canned answer, nothing recorded, nothing enforced --------------------


class StubPaymentGateway:
    """Always succeeds with a fixed reference, regardless of what it's asked to
    charge. Good enough when the test only cares about the RESULT of a successful
    charge (the order ending up PAID), not about what was actually sent.
    """

    async def charge(self, **kwargs) -> str:
        return "pay_stub_ref"

    async def refund(self, **kwargs) -> None:
        pass


async def test_stub_lets_the_happy_path_reach_paid_status(fake_uow, fake_clock, fake_lock) -> None:
    service = make_service(StubPaymentGateway(), fake_uow, fake_clock, fake_lock)

    order = await service.place_order(
        customer_ref="cust-1",
        requested_lines=[RequestedLine(product_id=1, quantity=2)],
        idempotency_key="key-1",
    )

    assert order.status.value == "paid"
    assert order.payment_reference == "pay_stub_ref"


# --- 3. Spy: records calls; the TEST decides what to check afterward --------------


class SpyPaymentGateway(StubPaymentGateway):
    """Everything a stub does, plus a memory of every call -- so the test can make
    assertions about HOW it was used, not just what it returned.
    """

    def __init__(self) -> None:
        self.charge_calls: list[dict] = []

    async def charge(self, **kwargs) -> str:
        self.charge_calls.append(kwargs)
        return await super().charge(**kwargs)


async def test_spy_proves_the_correct_amount_and_reference_were_sent(
    fake_uow, fake_clock, fake_lock
) -> None:
    gateway = SpyPaymentGateway()
    service = make_service(gateway, fake_uow, fake_clock, fake_lock)

    await service.place_order(
        customer_ref="cust-1",
        requested_lines=[RequestedLine(product_id=1, quantity=2)],
        idempotency_key="key-42",
    )

    assert len(gateway.charge_calls) == 1
    assert gateway.charge_calls[0]["amount_cents"] == 3_000  # 2 * 1500, zero tax
    assert gateway.charge_calls[0]["reference"] == "key-42"  # idempotency key, on purpose


# --- 4. Fake: a real (simplified) implementation, not just a canned answer --------


class FakePaymentGateway:
    """Unlike the stub, this one has actual DECISION logic -- it behaves like a
    (simplified) real payment processor: declines anything over $1,000. That's the
    difference between a fake and a stub: a stub returns the same thing regardless
    of input; a fake computes a real answer from its input.
    """

    async def charge(self, *, amount_cents: int, currency: str, reference: str) -> str:
        if amount_cents > 100_000:
            raise PaymentDeclinedError(reason="amount exceeds simulated limit")
        return f"pay_fake_{reference}"

    async def refund(self, **kwargs) -> None:
        pass


async def test_fake_actually_declines_large_amounts(fake_uow, fake_clock, fake_lock) -> None:
    fake_uow.seed_product(
        Product(
            id=2, sku="EXPENSIVE", name="Expensive Thing", unit_price_cents=200_000, stock_qty=5
        )
    )
    service = make_service(FakePaymentGateway(), fake_uow, fake_clock, fake_lock)

    with pytest.raises(PaymentDeclinedError):
        await service.place_order(
            customer_ref="cust-1",
            requested_lines=[RequestedLine(product_id=2, quantity=1)],
            idempotency_key="key-1",
        )


async def test_fake_approves_small_amounts_the_same_way_a_real_gateway_would(
    fake_uow, fake_clock, fake_lock
) -> None:
    service = make_service(FakePaymentGateway(), fake_uow, fake_clock, fake_lock)

    order = await service.place_order(
        customer_ref="cust-1",
        requested_lines=[RequestedLine(product_id=1, quantity=2)],
        idempotency_key="key-1",
    )

    assert order.payment_reference == "pay_fake_key-1"


# --- 5. Mock (Meszaros' strict sense): pre-programmed expectations, enforced ------


class ExpectingMockPaymentGateway:
    """Unlike a spy (record now, assert later), a strict mock is told what to expect
    UP FRONT, and fails the instant a call doesn't match -- or if `verify()` is
    never satisfied. This is what "mock" means in Meszaros' original taxonomy;
    `unittest.mock.Mock` (module 06) blends this with stub/spy behavior for
    convenience, which is exactly why it's worth seeing the strict version once.
    """

    def __init__(self, *, expected_amount_cents: int, expected_reference: str) -> None:
        self._expected_amount_cents = expected_amount_cents
        self._expected_reference = expected_reference
        self._charge_was_called = False

    async def charge(self, *, amount_cents: int, currency: str, reference: str) -> str:
        assert amount_cents == self._expected_amount_cents, (
            f"expected a charge of {self._expected_amount_cents}, got {amount_cents}"
        )
        assert reference == self._expected_reference, (
            f"expected reference {self._expected_reference!r}, got {reference!r}"
        )
        self._charge_was_called = True
        return "pay_mock_ref"

    async def refund(self, **kwargs) -> None:
        raise AssertionError("refund() was not expected in this test")

    def verify(self) -> None:
        assert self._charge_was_called, "expected charge() to be called, but it never was"


async def test_strict_mock_enforces_the_call_shape_up_front(
    fake_uow, fake_clock, fake_lock
) -> None:
    gateway = ExpectingMockPaymentGateway(expected_amount_cents=3_000, expected_reference="key-1")
    service = make_service(gateway, fake_uow, fake_clock, fake_lock)

    await service.place_order(
        customer_ref="cust-1",
        requested_lines=[RequestedLine(product_id=1, quantity=2)],
        idempotency_key="key-1",
    )

    gateway.verify()
