"""Basic respx route matching, and asserting on the real request that was sent."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from shop.gateways.payments import HttpPaymentGateway

BASE_URL = "https://payments.example.com"


@respx.mock
async def test_charge_success_hits_the_right_route() -> None:
    route = respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(201, json={"payment_reference": "pay_abc"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    reference = await gateway.charge(amount_cents=3_000, currency="usd", reference="key-1")

    assert reference == "pay_abc"
    assert route.called
    await client.aclose()


@respx.mock
async def test_the_actual_request_body_sent() -> None:
    """The `request` here is a REAL httpx.Request, built by REAL httpx code from
    HttpPaymentGateway's arguments -- not something our own code handed a mock.
    """
    route = respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(201, json={"payment_reference": "pay_abc"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    await gateway.charge(amount_cents=3_000, currency="usd", reference="key-1")

    sent_request = route.calls.last.request
    assert json.loads(sent_request.content) == {
        "amount_cents": 3_000,
        "currency": "usd",
        "reference": "key-1",
    }
    assert sent_request.headers["Authorization"] == "Bearer secret-key"
    await client.aclose()


@respx.mock
async def test_refund_hits_the_right_route_with_the_reference_in_the_path() -> None:
    route = respx.post(f"{BASE_URL}/v1/charges/pay_abc/refunds").mock(
        return_value=httpx.Response(200, json={})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    await gateway.refund(payment_reference="pay_abc", amount_cents=1_000)

    assert route.called
    assert json.loads(route.calls.last.request.content) == {"amount_cents": 1_000}
    await client.aclose()


@respx.mock
async def test_a_request_to_an_undeclared_route_raises() -> None:
    """No routes declared at all: respx (in its default "assert all mocked" mode)
    raises rather than letting the request fall through to the real network. This is
    a safety net, not just a matching mechanism -- a test that FORGOT to mock a route
    fails loudly instead of making a real HTTP call during your test run.
    """
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = HttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(respx.models.AllMockedAssertionError, match="not mocked"):
        await gateway.charge(amount_cents=100, currency="usd", reference="key-1")

    await client.aclose()
