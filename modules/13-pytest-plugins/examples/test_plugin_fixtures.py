"""No conftest.py in this directory. `fake_clock`, `fake_uow`, `fake_lock`,
`fake_gateway`, and `product_factory` all come from `testkit`'s pytest11 plugin
(pyproject.toml + testkit/plugin.py) -- installed once, available everywhere.

Compare this file directly against modules/05-test-double-taxonomy/examples/conftest.py:
same fakes, zero local plumbing.

Try:
    uv run pytest modules/13-pytest-plugins/examples/test_plugin_fixtures.py \
        --fake-now=2030-06-15 -v
and watch test_fake_clock_uses_the_cli_option's assertion follow the flag.
"""

from __future__ import annotations

from datetime import UTC, datetime

from testkit.factories import ProductFactory
from testkit.fakes import FakeClock, FakeIdempotencyLock, FakePaymentGateway, FakeUnitOfWork

from shop.domain.models import RequestedLine
from shop.services.orders import OrderService


def test_fake_clock_default(fake_clock: FakeClock) -> None:
    assert fake_clock.now() == datetime(2026, 1, 1, tzinfo=UTC)


def test_fake_clock_uses_the_cli_option(fake_clock: FakeClock, request) -> None:
    """The value here depends entirely on what --fake-now was passed on the command
    line (default shown by test_fake_clock_default above) -- this is
    pytest_addoption (testkit/plugin.py) feeding a fixture, end to end.
    """
    configured = request.config.getoption("--fake-now")
    assert fake_clock.now() == datetime.fromisoformat(configured)


def test_product_factory_builds_a_valid_product(product_factory: type[ProductFactory]) -> None:
    product = product_factory.build(sku="PLUGIN-TEST", stock_qty=10, unit_price_cents=500)

    assert product.sku == "PLUGIN-TEST"
    assert product.stock_qty == 10


async def test_full_order_service_from_testkit_fakes_alone(
    fake_uow: FakeUnitOfWork,
    fake_clock: FakeClock,
    fake_lock: FakeIdempotencyLock,
    fake_gateway: FakePaymentGateway,
    product_factory: type[ProductFactory],
) -> None:
    """The same shape of test as modules/05-test-double-taxonomy/examples/test_five_ways.py,
    with every fake supplied by the plugin instead of a local conftest.py.
    """
    product = fake_uow.seed_product(
        product_factory.build(unit_price_cents=1_000, stock_qty=5)
    )
    service = OrderService(
        uow_factory=fake_uow,
        payment_gateway=fake_gateway,
        idempotency_lock=fake_lock,
        clock=fake_clock,
        tax_rate=0.0,
    )

    order = await service.place_order(
        customer_ref="cust-1",
        requested_lines=[RequestedLine(product_id=product.id, quantity=2)],
        idempotency_key="plugin-key-1",
    )

    assert order.status.value == "paid"
    assert order.created_at == fake_clock.now()
