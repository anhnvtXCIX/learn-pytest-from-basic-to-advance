"""Reference solution for exercises/test_respx.py."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from shop.domain.errors import PaymentDeclinedError, PaymentGatewayUnavailableError
from shop.gateways.payments import HttpPaymentGateway

BASE_URL = "https://payments.example.com"


@respx.mock
async def test_charge_sends_the_correct_body_and_returns_the_reference() -> None:
    route = respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(201, json={"payment_reference": "pay_xyz"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    reference = await gateway.charge(amount_cents=5_000, currency="eur", reference="order-9")

    assert reference == "pay_xyz"
    assert json.loads(route.calls.last.request.content) == {
        "amount_cents": 5_000,
        "currency": "eur",
        "reference": "order-9",
    }
    await client.aclose()


@respx.mock
async def test_402_raises_payment_declined() -> None:
    respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(402, json={"reason": "fraud suspected"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentDeclinedError, match="fraud suspected"):
        await gateway.charge(amount_cents=1_000, currency="usd", reference="key-1")

    await client.aclose()


@respx.mock
async def test_refund_timeout_raises_payment_gateway_unavailable() -> None:
    respx.post(f"{BASE_URL}/v1/charges/pay_abc/refunds").mock(
        side_effect=httpx.TimeoutException("timed out")
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentGatewayUnavailableError):
        await gateway.refund(payment_reference="pay_abc", amount_cents=500)

    await client.aclose()
