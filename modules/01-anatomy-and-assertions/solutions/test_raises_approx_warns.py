"""Reference solution for exercises/test_raises_approx_warns.py."""

from __future__ import annotations

import warnings

import pytest

from shop.domain.errors import InvalidOrderError, PaymentDeclinedError
from shop.domain.pricing import calculate_discount_cents


def charge(amount_cents: int) -> str:
    if amount_cents > 100_000:
        raise PaymentDeclinedError(reason="amount exceeds limit")
    return "pay_ok"


def test_charge_over_limit_raises_payment_declined() -> None:
    with pytest.raises(PaymentDeclinedError) as excinfo:
        charge(150_000)

    assert excinfo.value.reason == "amount exceeds limit"


def test_discount_rate_as_a_percentage() -> None:
    subtotal = 10_000
    discount = calculate_discount_cents(subtotal)

    effective_rate = discount / subtotal

    assert effective_rate == pytest.approx(0.10)


def test_negative_subtotal_raises_invalid_order_error() -> None:
    with pytest.raises(InvalidOrderError, match="negative"):
        calculate_discount_cents(-100)


def _old_calculate_discount(subtotal_cents: int) -> int:
    warnings.warn(
        "_old_calculate_discount is deprecated, use calculate_discount_cents",
        DeprecationWarning,
        stacklevel=2,
    )
    return calculate_discount_cents(subtotal_cents)


def test_old_calculate_discount_warns() -> None:
    with pytest.warns(DeprecationWarning, match="deprecated"):
        _old_calculate_discount(10_000)
