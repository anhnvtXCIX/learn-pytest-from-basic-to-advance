"""Exercise: use testkit's fixtures (no local conftest.py needed for these), and
implement conftest.py's TODOs for the addoption/ordering tests below.

    make ex M=13
"""

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
    """TODO: seed a product via fake_uow.seed_product(product_factory.build(...)),
    build an OrderService from the fixtures above (tax_rate=0.0), place_order for
    quantity=1, then cancel_order it. Assert the final status is "refunded" and that
    fake_gateway.refund_calls has exactly one entry.
    """
    product = fake_uow.seed_product(product_factory.build(sku="NOPE"))
    service = OrderService(
        uow_factory=fake_uow,
        payment_gateway=fake_gateway,
        idempotency_lock=fake_lock,
        clock=fake_clock,
        tax_rate=0.0,
    )

    order = await service.place_order(
        customer_ref="abc",
        requested_lines=[RequestedLine(product_id=product.id, quantity=1)],
        idempotency_key="key-1",
    )

    if order.id:
        canceled_order = await service.cancel_order(order_id=order.id)

        assert canceled_order.status == "refunded"
        assert len(fake_gateway.refund_calls) == 1


def test_stock_qty_cli_option(request) -> None:
    """TODO (after implementing pytest_addoption in conftest.py): read
    request.config.getoption("--stock-qty"), convert it to int, and assert it's
    10 by default. Then try:
        uv run pytest modules/13-pytest-plugins/exercises --stock-qty=25 -m exercise -v
    and confirm the assertion would need to change to 25 to still pass (you don't
    need to make the test handle both -- just confirm you understand why it's 25
    with the flag and 10 without it).
    """
    stock_qty = request.config.getoption("--stock-qty")

    assert stock_qty == 10


def test_zzz_ordering_placeholder_a() -> None:
    pass


def test_zzz_ordering_placeholder_should_run_last() -> None:
    """TODO (after implementing the sort in conftest.py): this test's name contains
    "zzz", same as the one above it -- run
        uv run pytest modules/13-pytest-plugins/exercises --collect-only -q -m exercise
    a few times and confirm both "zzz" tests land at the end, in SOME consistent
    relative position, however pytest-randomly orders everything else.
    """
