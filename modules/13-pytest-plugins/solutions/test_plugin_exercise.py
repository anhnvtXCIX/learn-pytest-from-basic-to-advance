"""Reference solution for exercises/test_plugin_exercise.py."""

from __future__ import annotations

from testkit.factories import ProductFactory
from testkit.fakes import FakeClock, FakeIdempotencyLock, FakePaymentGateway, FakeUnitOfWork

from shop.domain.models import RequestedLine
from shop.services.orders import OrderService


async def test_cancel_flow_using_testkit_fixtures(
    fake_uow: FakeUnitOfWork,
    fake_clock: FakeClock,
    fake_lock: FakeIdempotencyLock,
    fake_gateway: FakePaymentGateway,
    product_factory: type[ProductFactory],
) -> None:
    product = fake_uow.seed_product(product_factory.build(unit_price_cents=1_000, stock_qty=5))
    service = OrderService(
        uow_factory=fake_uow,
        payment_gateway=fake_gateway,
        idempotency_lock=fake_lock,
        clock=fake_clock,
        tax_rate=0.0,
    )

    order = await service.place_order(
        customer_ref="cust-1",
        requested_lines=[RequestedLine(product_id=product.id, quantity=1)],
        idempotency_key="exercise-key",
    )
    cancelled = await service.cancel_order(order.id)

    assert cancelled.status.value == "refunded"
    assert len(fake_gateway.refund_calls) == 1


def test_stock_qty_cli_option(request) -> None:
    assert int(request.config.getoption("--stock-qty")) == 10


def test_zzz_ordering_placeholder_a() -> None:
    pass


def test_zzz_ordering_placeholder_should_run_last() -> None:
    pass
