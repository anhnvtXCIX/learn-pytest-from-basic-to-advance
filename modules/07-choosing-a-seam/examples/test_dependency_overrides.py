"""FastAPI's dependency_overrides: DI at the HTTP layer. Module 11 uses this at full
scale (real DB, real service, only the payment gateway faked); here's the minimal
version, overriding the whole `OrderService` to keep this file self-contained.
"""

from __future__ import annotations

from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient

from shop.api.app import create_app
from shop.api.deps import get_order_service
from shop.config import Settings
from shop.domain.models import Order, OrderLine, OrderStatus, OrderTotals


class FakeOrderService:
    def __init__(self, order: Order) -> None:
        self._order = order

    async def get_order(self, order_id: int) -> Order:
        assert order_id == self._order.id
        return self._order


async def test_dependency_override_replaces_the_real_order_service() -> None:
    settings = Settings()
    app = create_app(settings)

    fake_order = Order(
        id=1,
        customer_ref="cust-1",
        status=OrderStatus.PAID,
        lines=[OrderLine(product_id=1, quantity=1, unit_price_cents=1_000)],
        totals=OrderTotals(subtotal_cents=1_000, discount_cents=0, tax_cents=0, total_cents=1_000),
        idempotency_key="key-1",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        payment_reference="pay_abc",
    )
    # This is the entire technique: map the DEPENDENCY FUNCTION (not a string path,
    # not an instance) to a zero-argument callable that returns the replacement.
    app.dependency_overrides[get_order_service] = lambda: FakeOrderService(fake_order)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/orders/1", headers={"X-API-Key": settings.api_key})

    assert response.status_code == 200
    assert response.json()["payment_reference"] == "pay_abc"
    # Notice: no database, no Redis, no HTTP payment gateway were ever touched --
    # `create_app`'s lifespan still builds them (they're needed for OTHER
    # dependencies), but this specific route never reaches them because
    # get_order_service was overridden before any request was made.
