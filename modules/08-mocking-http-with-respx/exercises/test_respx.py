"""Exercise: respx route matching, request assertions, error simulation.

    make ex M=08
"""

from __future__ import annotations

import respx

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
    raise NotImplementedError("write this test")


@respx.mock
async def test_402_raises_payment_declined() -> None:
    """TODO: mock a 402 response with json={"reason": "fraud suspected"}, call
    charge(), and assert PaymentDeclinedError is raised with a message matching
    "fraud suspected".
    """
    raise NotImplementedError("write this test")


@respx.mock
async def test_refund_timeout_raises_payment_gateway_unavailable() -> None:
    """TODO: mock the refund route (POST {BASE_URL}/v1/charges/pay_abc/refunds) with
    side_effect=httpx.TimeoutException("timed out"), call
    gateway.refund(payment_reference="pay_abc", amount_cents=500), and assert
    PaymentGatewayUnavailableError is raised.
    """
    raise NotImplementedError("write this test")
