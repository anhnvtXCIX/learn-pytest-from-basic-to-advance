"""`create_autospec`: constrains a mock to the real object's actual shape."""

from __future__ import annotations

from unittest.mock import create_autospec

import pytest

from shop.gateways.payments import HttpPaymentGateway


def test_autospec_catches_a_typo_d_method_name() -> None:
    mock_gateway = create_autospec(HttpPaymentGateway, instance=True)

    with pytest.raises(AttributeError):
        mock_gateway.chrage(amount_cents=100, currency="usd", reference="key-1")  # typo


def test_autospec_catches_a_wrong_signature() -> None:
    mock_gateway = create_autospec(HttpPaymentGateway, instance=True)

    with pytest.raises(TypeError):
        mock_gateway.charge(amount_cents=100)  # missing required currency, reference


async def test_autospec_infers_asyncmock_for_async_methods() -> None:
    """No need to remember to use AsyncMock yourself -- create_autospec looks at the
    real class, sees `charge` and `refund` are `async def`, and builds AsyncMocks for
    them automatically. If it hadn't, `await mock_gateway.charge(...)` below would
    raise TypeError ("can't be used in 'await' expression"), the same failure
    test_mock_and_asyncmock_basics.py demonstrates directly on a bare `Mock`.
    """
    mock_gateway = create_autospec(HttpPaymentGateway, instance=True)
    mock_gateway.charge.return_value = "pay_ref"

    result = await mock_gateway.charge(amount_cents=100, currency="usd", reference="key-1")

    assert result == "pay_ref"
    mock_gateway.charge.assert_awaited_once_with(
        amount_cents=100, currency="usd", reference="key-1"
    )


def test_spec_set_catches_setting_a_nonexistent_attribute() -> None:
    mock_gateway = create_autospec(HttpPaymentGateway, instance=True, spec_set=True)

    with pytest.raises(AttributeError):
        mock_gateway.nonexistent_attribute = "oops"  # not a real attribute on HttpPaymentGateway
