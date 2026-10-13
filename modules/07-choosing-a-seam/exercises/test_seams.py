"""Exercise: monkeypatch, freezegun, dependency_overrides.

make ex M=07
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from freezegun import freeze_time
from httpx import ASGITransport, AsyncClient

from shop.api.app import create_app
from shop.api.deps import get_order_service
from shop.clock import SystemClock
from shop.config import Settings
from shop.domain.errors import OrderNotFoundError


def test_monkeypatch_setenv_changes_a_freshly_constructed_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TODO: use monkeypatch.setenv to set SHOP_PAYMENT_GATEWAY_URL to
    "https://sandbox.example.com", construct a fresh Settings(), and assert its
    payment_gateway_url field equals that value.
    """
    monkeypatch.setenv("SHOP_PAYMENT_GATEWAY_URL", "https://sandbox.example.com")

    settings = Settings()

    assert settings.payment_gateway_url == "https://sandbox.example.com"


def test_freezegun_freezes_system_clock_at_a_specific_instant() -> None:
    """TODO: use freeze_time to freeze at "2031-03-03 09:30:00" and assert
    SystemClock().now() equals datetime(2031, 3, 3, 9, 30, 0, tzinfo=UTC).
    """
    with freeze_time("2031-03-03 09:30:00"):
        assert SystemClock().now() == datetime(2031, 3, 3, 9, 30, 0, tzinfo=UTC)


class FakeOrderServiceThatRaisesNotFound:
    async def get_order(self, order_id: int):
        raise OrderNotFoundError(order_id)


async def test_dependency_override_can_simulate_an_error_path() -> None:
    """TODO: create_app(), override get_order_service with a lambda returning
    FakeOrderServiceThatRaisesNotFound(), make a GET request to /orders/999 (with the
    correct X-API-Key header, see Settings().api_key), and assert the response
    status code is 404. This proves you can test error-handling paths in routes.py
    without ever needing a database that's missing a row.
    """
    settings = Settings()
    app = create_app(settings)

    app.dependency_overrides[get_order_service] = lambda: FakeOrderServiceThatRaisesNotFound()

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/orders/999", headers={"X-API-Key": settings.api_key})

    assert response.status_code == 404
