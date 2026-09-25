"""pytest-mock's `mocker` fixture: same unittest.mock machinery, automatic cleanup.

`HttpPaymentGateway` takes its `httpx.AsyncClient` as a constructor argument (module
07 calls this "choosing a seam") -- so there's no import path to patch at all here,
just an object to hand it directly. That's the preferred approach in this repo. This
file mocks the *client itself* to show `create_autospec` + `mocker` working together
on a real third-party class, which is the situation you're in whenever DI isn't
available (e.g. mocking a library's internals you don't control the construction of).
"""

from __future__ import annotations

from unittest.mock import create_autospec

import httpx
import pytest

from shop.domain.errors import PaymentDeclinedError
from shop.gateways.payments import HttpPaymentGateway


@pytest.fixture
def mock_client(mocker) -> httpx.AsyncClient:
    """create_autospec on httpx.AsyncClient itself: `.post` is correctly inferred as
    an AsyncMock because it's `async def` on the real class.
    """
    return create_autospec(httpx.AsyncClient, instance=True)


def _fake_response(status_code: int, payload: dict) -> httpx.Response:
    return httpx.Response(status_code=status_code, json=payload, request=httpx.Request("POST", "http://test"))


async def test_mocker_patch_is_undone_automatically(mocker) -> None:
    """No `with patch(...):` block, no explicit `.stop()` -- pytest-mock restores
    whatever `mocker.patch` touched at the end of THIS test, pass or fail.
    """
    mocker.patch("shop.config.get_settings", return_value="patched")

    from shop.config import get_settings

    assert get_settings() == "patched"
    # No cleanup code here -- and the next test in this file proves it wasn't needed:


def test_the_previous_patch_did_not_leak_into_this_test() -> None:
    from shop.config import get_settings

    settings = get_settings()
    assert settings.api_key == "test-client-api-key"  # the REAL Settings, not "patched"


async def test_gateway_charge_posts_the_right_body(mock_client: httpx.AsyncClient) -> None:
    mock_client.post.return_value = _fake_response(201, {"payment_reference": "pay_abc"})
    gateway = HttpPaymentGateway(mock_client, api_key="secret-key")

    reference = await gateway.charge(amount_cents=3_000, currency="usd", reference="key-1")

    assert reference == "pay_abc"
    mock_client.post.assert_awaited_once_with(
        "/v1/charges",
        json={"amount_cents": 3_000, "currency": "usd", "reference": "key-1"},
        headers={"Authorization": "Bearer secret-key"},
    )


async def test_gateway_translates_402_to_payment_declined(mock_client: httpx.AsyncClient) -> None:
    mock_client.post.return_value = _fake_response(402, {"reason": "insufficient funds"})
    gateway = HttpPaymentGateway(mock_client, api_key="secret-key")

    with pytest.raises(PaymentDeclinedError, match="insufficient funds"):
        await gateway.charge(amount_cents=3_000, currency="usd", reference="key-1")
