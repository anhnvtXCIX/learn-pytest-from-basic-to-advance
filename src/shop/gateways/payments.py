"""The one external HTTP dependency in this whole app.

`PaymentGateway` is a `Protocol`, not an abstract base class: `OrderService` (and its
tests) only care that something has these two async methods, not that it inherits from
anything in particular. That's what lets module 05 hand it a hand-written `FakePaymentGateway`
and module 08 hand it a real `HttpPaymentGateway` pointed at a respx-mocked URL, with
`OrderService` none the wiser either way. This is "don't mock what you don't own"
(see docs/02-test-doubles.md): we don't reach into `httpx` internals in tests, we
substitute our own small interface at the boundary we *do* own.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from shop.domain.errors import PaymentDeclinedError, PaymentGatewayUnavailableError


class PaymentGateway(Protocol):
    async def charge(self, *, amount_cents: int, currency: str, reference: str) -> str:
        """Charge a card and return a payment reference. Raises
        `PaymentDeclinedError` or `PaymentGatewayUnavailableError`.
        """
        ...

    async def refund(self, *, payment_reference: str, amount_cents: int) -> None:
        """Raises `PaymentGatewayUnavailableError` on failure."""
        ...


class HttpPaymentGateway:
    """Talks to a (fictional) REST payment processor over HTTP."""

    def __init__(self, client: httpx.AsyncClient, *, api_key: str) -> None:
        self._client = client
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def charge(self, *, amount_cents: int, currency: str, reference: str) -> str:
        try:
            response = await self._client.post(
                "/v1/charges",
                json={"amount_cents": amount_cents, "currency": currency, "reference": reference},
                headers=self._headers(),
            )
        except httpx.TimeoutException as exc:
            raise PaymentGatewayUnavailableError("timed out") from exc
        except httpx.TransportError as exc:
            raise PaymentGatewayUnavailableError(str(exc)) from exc

        if response.status_code == 402:
            raise PaymentDeclinedError(response.json().get("reason", "declined"))
        if response.status_code >= 500:
            raise PaymentGatewayUnavailableError(f"HTTP {response.status_code}")
        response.raise_for_status()
        return str(response.json()["payment_reference"])

    async def refund(self, *, payment_reference: str, amount_cents: int) -> None:
        try:
            response = await self._client.post(
                f"/v1/charges/{payment_reference}/refunds",
                json={"amount_cents": amount_cents},
                headers=self._headers(),
            )
        except httpx.TimeoutException as exc:
            raise PaymentGatewayUnavailableError("timed out") from exc
        except httpx.TransportError as exc:
            raise PaymentGatewayUnavailableError(str(exc)) from exc

        if response.status_code >= 500:
            raise PaymentGatewayUnavailableError(f"HTTP {response.status_code}")
        response.raise_for_status()
