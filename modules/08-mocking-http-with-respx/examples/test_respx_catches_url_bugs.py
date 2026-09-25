"""The concrete case for respx over a mocked client: a URL bug that a fully-mocked
`httpx.AsyncClient` (module 06's `create_autospec` approach) cannot catch, because
mocking the client away also mocks away the URL-construction logic that has the bug.
"""

from __future__ import annotations

from unittest.mock import create_autospec

import httpx
import pytest
import respx

BASE_URL = "https://payments.example.com"


class BrokenHttpPaymentGateway:
    """Same shape as the real HttpPaymentGateway, with one deliberate bug: a typo'd
    path (`/v1/charge` instead of `/v1/charges`). Everything else is identical.
    """

    def __init__(self, client: httpx.AsyncClient, *, api_key: str) -> None:
        self._client = client
        self._api_key = api_key

    async def charge(self, *, amount_cents: int, currency: str, reference: str) -> str:
        response = await self._client.post(
            "/v1/charge",  # BUG: should be "/v1/charges"
            json={"amount_cents": amount_cents, "currency": currency, "reference": reference},
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        return str(response.json()["payment_reference"])


async def test_a_fully_mocked_client_does_not_notice_the_wrong_url() -> None:
    """This test PASSES despite the bug -- proving the limitation, not a good
    pattern to copy. `create_autospec` replaces `.post` entirely; nothing here ever
    asks httpx to actually resolve a URL, so a wrong path is invisible to it.
    """
    mock_client = create_autospec(httpx.AsyncClient, instance=True)
    mock_response = httpx.Response(
        201, json={"payment_reference": "pay_abc"}, request=httpx.Request("POST", BASE_URL)
    )
    mock_client.post.return_value = mock_response
    gateway = BrokenHttpPaymentGateway(mock_client, api_key="secret-key")

    reference = await gateway.charge(amount_cents=1_000, currency="usd", reference="key-1")

    assert reference == "pay_abc"  # "passes" -- the bug is completely invisible here


@respx.mock
async def test_respx_catches_the_same_bug() -> None:
    """Only the CORRECT path is mocked -- exactly what a real test would declare,
    matching the real gateway's contract. The broken gateway posts to the wrong
    path, respx has no route for it, and the request fails loudly.
    """
    respx.post(f"{BASE_URL}/v1/charges").mock(
        return_value=httpx.Response(201, json={"payment_reference": "pay_abc"})
    )
    client = httpx.AsyncClient(base_url=BASE_URL)
    gateway = BrokenHttpPaymentGateway(client, api_key="secret-key")

    with pytest.raises(respx.models.AllMockedAssertionError):
        await gateway.charge(amount_cents=1_000, currency="usd", reference="key-1")

    await client.aclose()
