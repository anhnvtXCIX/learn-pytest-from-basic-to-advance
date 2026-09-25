"""Simulating timeouts and 5xx, and confirming HttpPaymentGateway's translation to
this repo's own domain exceptions -- that translation is exactly what this file's
job is to test; OrderService never sees an httpx exception (see services/orders.py).
"""

from __future__ import annotations

import httpx
import pytest
import respx

from shop.domain.errors import PaymentDeclinedError, PaymentGatewayUnavailableError
from shop.gateways.payments import HttpPaymentGateway

BASE_URL = "https://payments.example.com"


@respx.mock
async def test_timeout_becomes_payment_gateway_unavailable() -> None:
    respx.post(f"{BASE_URL}/v1/charges").mock(side_effect=httpx.TimeoutException("timed out"))
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentGatewayUnavailableError, match="timed out"):
        await gateway.charge(amount_cents=1_000, currency="usd", reference="key-1")

    await client.aclose()


@respx.mock
async def test_connection_error_becomes_payment_gateway_unavailable() -> None:
    respx.post(f"{BASE_URL}/v1/charges").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentGatewayUnavailableError):
        await gateway.charge(amount_cents=1_000, currency="usd", reference="key-1")

    await client.aclose()


@respx.mock
async def test_500_becomes_payment_gateway_unavailable() -> None:
    respx.post(f"{BASE_URL}/v1/charges").mock(return_value=httpx.Response(500))
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentGatewayUnavailableError, match="HTTP 500"):
        await gateway.charge(amount_cents=1_000, currency="usd", reference="key-1")

    await client.aclose()


@respx.mock
async def test_402_becomes_payment_declined_with_the_reason_from_the_body() -> None:
    """A 402 is NOT a transport-level failure -- httpx doesn't raise for it, we have
    to check the status code ourselves. This is a different code path in
    HttpPaymentGateway than the timeout/5xx cases above; worth its own test.
    """
    respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(402, json={"reason": "card expired"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentDeclinedError, match="card expired"):
        await gateway.charge(amount_cents=1_000, currency="usd", reference="key-1")

    await client.aclose()


@respx.mock
async def test_refund_500_also_becomes_payment_gateway_unavailable() -> None:
    respx.post(f"{BASE_URL}/v1/charges/pay_abc/refunds").mock(return_value=httpx.Response(503))
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(PaymentGatewayUnavailableError, match="HTTP 503"):
        await gateway.refund(payment_reference="pay_abc", amount_cents=1_000)

    await client.aclose()
