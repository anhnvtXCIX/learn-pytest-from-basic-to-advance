"""Exercise: respx route matching, request assertions, error simulation.

make ex M=08
"""

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
    """TODO:
    1. Declare a respx route for POST {BASE_URL}/v1/charges that returns a 201 with
       json={"payment_reference": "pay_xyz"}.
    2. Build an httpx.AsyncClient(base_url=BASE_URL) and an HttpPaymentGateway with it.
    3. Call gateway.charge(amount_cents=5_000, currency="eur", reference="order-9").
    4. Assert the returned reference is "pay_xyz".
    5. Assert the request that was actually sent (route.calls.last.request) has a
       JSON body matching {"amount_cents": 5000, "currency": "eur", "reference": "order-9"}.
    Don't forget to `await client.aclose()` at the end.
    """
    route = respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(201, json={"payment_reference": "pay_xyz"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    reference = await gateway.charge(amount_cents=5_000, currency="eur", reference="order-9")

    assert reference == "pay_xyz"
    assert json.loads(route.calls.last.request.content) == {
        "amount_cents": 5000,
        "currency": "eur",
        "reference": "order-9",
    }

    await client.aclose()


@respx.mock
async def test_402_raises_payment_declined() -> None:
    """TODO: mock a 402 response with json={"reason": "fraud suspected"}, call
    charge(), and assert PaymentDeclinedError is raised with a message matching
    "fraud suspected".
    """
    respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(402, json={"reason": "fraud suspected"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentDeclinedError, match="fraud suspected"):
        await gateway.charge(amount_cents=5_000, currency="eur", reference="order-9")

    await client.aclose()


@respx.mock
async def test_refund_timeout_raises_payment_gateway_unavailable() -> None:
    """TODO: mock the refund route (POST {BASE_URL}/v1/charges/pay_abc/refunds) with
    side_effect=httpx.TimeoutException("timed out"), call
    gateway.refund(payment_reference="pay_abc", amount_cents=500), and assert
    PaymentGatewayUnavailableError is raised.
    """
    respx.post(f"{BASE_URL}/v1/charges/pay_abc/refunds").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentGatewayUnavailableError, match="timed out"):
        await gateway.refund(payment_reference="pay_abc", amount_cents=500)

    await client.aclose()
